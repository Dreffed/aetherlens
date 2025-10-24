-- Migration: 004_continuous_aggregates
-- Description: Create continuous aggregates for hourly and daily metrics
-- Date: 2025-10-24
-- Author: AetherLens Team

-- ============================================================================
-- 1. HOURLY METRICS AGGREGATE
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    device_id,
    metric_type,
    COUNT(*) as sample_count,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    SUM(value) as sum_value,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY value) as p50_value,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY value) as p95_value,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY value) as p99_value,
    STDDEV(value) as stddev_value
FROM metrics
GROUP BY hour, device_id, metric_type
WITH NO DATA;

COMMENT ON MATERIALIZED VIEW metrics_hourly IS 'Hourly aggregated metrics with statistics';

-- Add refresh policy (refresh every hour, with 1 hour lag)
SELECT add_continuous_aggregate_policy('metrics_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- ============================================================================
-- 2. DAILY METRICS AGGREGATE
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    device_id,
    metric_type,
    COUNT(*) as sample_count,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    SUM(CASE WHEN metric_type = 'energy' THEN value ELSE 0 END) as total_energy,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY value) as median_value
FROM metrics
GROUP BY day, device_id, metric_type
WITH NO DATA;

COMMENT ON MATERIALIZED VIEW metrics_daily IS 'Daily aggregated metrics';

-- Add refresh policy (refresh daily, with 1 day lag)
SELECT add_continuous_aggregate_policy('metrics_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- ============================================================================
-- 3. HOURLY COST AGGREGATE
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS cost_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    device_id,
    COUNT(*) as calculation_count,
    SUM(energy_kwh) as total_energy_kwh,
    SUM(cost_total) as total_cost,
    AVG(cost_total) as avg_cost,
    AVG(rate_per_kwh) as avg_rate_per_kwh,
    MAX(peak_power_w) as max_peak_power,
    SUM(carbon_co2_kg) as total_carbon_kg
FROM cost_calculations
GROUP BY hour, device_id
WITH NO DATA;

COMMENT ON MATERIALIZED VIEW cost_hourly IS 'Hourly cost aggregates';

-- Add refresh policy
SELECT add_continuous_aggregate_policy('cost_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- ============================================================================
-- 4. DAILY COST AGGREGATE
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS cost_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    device_id,
    SUM(energy_kwh) as total_energy_kwh,
    SUM(cost_total) as total_cost,
    SUM(cost_energy) as total_cost_energy,
    SUM(cost_demand) as total_cost_demand,
    SUM(cost_taxes) as total_cost_taxes,
    AVG(rate_per_kwh) as avg_rate_per_kwh,
    MAX(peak_power_w) as daily_peak_power,
    SUM(carbon_co2_kg) as total_carbon_kg,
    COUNT(DISTINCT rate_period) as rate_periods_used
FROM cost_calculations
GROUP BY day, device_id
WITH NO DATA;

COMMENT ON MATERIALIZED VIEW cost_daily IS 'Daily cost summaries';

-- Add refresh policy
SELECT add_continuous_aggregate_policy('cost_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- ============================================================================
-- 5. CREATE INDEXES ON CONTINUOUS AGGREGATES
-- ============================================================================

-- Indexes for hourly metrics
CREATE INDEX IF NOT EXISTS idx_metrics_hourly_device_hour
ON metrics_hourly (device_id, hour DESC);

CREATE INDEX IF NOT EXISTS idx_metrics_hourly_type_hour
ON metrics_hourly (metric_type, hour DESC);

-- Indexes for daily metrics
CREATE INDEX IF NOT EXISTS idx_metrics_daily_device_day
ON metrics_daily (device_id, day DESC);

CREATE INDEX IF NOT EXISTS idx_metrics_daily_type_day
ON metrics_daily (metric_type, day DESC);

-- Indexes for hourly costs
CREATE INDEX IF NOT EXISTS idx_cost_hourly_device_hour
ON cost_hourly (device_id, hour DESC);

-- Indexes for daily costs
CREATE INDEX IF NOT EXISTS idx_cost_daily_device_day
ON cost_daily (device_id, day DESC);

-- ============================================================================
-- 6. VERIFY CONTINUOUS AGGREGATES
-- ============================================================================

SELECT view_name, materialization_hypertable_name, refresh_lag
FROM timescaledb_information.continuous_aggregates
WHERE view_schema = 'public';

-- ============================================================================
-- 7. RECORD MIGRATION
-- ============================================================================
INSERT INTO migration_history (version, description)
VALUES ('004', 'Create continuous aggregates - hourly and daily views')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
DECLARE
    cagg_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO cagg_count
    FROM timescaledb_information.continuous_aggregates
    WHERE view_schema = 'public';

    RAISE NOTICE '✅ Migration 004_continuous_aggregates completed successfully';
    RAISE NOTICE 'Continuous aggregates created: %', cagg_count;
    RAISE NOTICE 'Views: metrics_hourly, metrics_daily, cost_hourly, cost_daily';
    RAISE NOTICE 'Refresh policies configured:';
    RAISE NOTICE '  - Hourly views: refresh every 1 hour';
    RAISE NOTICE '  - Daily views: refresh every 1 day';
    RAISE NOTICE 'These views will automatically maintain aggregated data!';
END $$;
