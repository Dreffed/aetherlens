-- Migration: 002_create_hypertables
-- Description: Create metrics hypertable for time-series data
-- Date: 2025-10-24
-- Author: AetherLens Team

-- ============================================================================
-- 1. METRICS TABLE (Main time-series table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS metrics (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(20) NOT NULL,
    tags JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE metrics IS 'Time-series metrics from all devices';
COMMENT ON COLUMN metrics.time IS 'Timestamp of the metric (indexed for time-series queries)';
COMMENT ON COLUMN metrics.device_id IS 'Foreign key to devices table';
COMMENT ON COLUMN metrics.metric_type IS 'Type of metric (power, energy, temperature, etc.)';
COMMENT ON COLUMN metrics.value IS 'Numeric value of the metric';
COMMENT ON COLUMN metrics.unit IS 'Unit of measurement (watts, kwh, celsius, etc.)';
COMMENT ON COLUMN metrics.tags IS 'Additional tags for filtering (room, circuit, user, etc.)';
COMMENT ON COLUMN metrics.metadata IS 'Collection metadata (quality_score, source, duration_ms)';

-- ============================================================================
-- 2. CONVERT TO HYPERTABLE
-- ============================================================================
-- Create hypertable with 7-day chunks
SELECT create_hypertable(
    'metrics',
    'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ============================================================================
-- 3. ADD FOREIGN KEY CONSTRAINT
-- ============================================================================
ALTER TABLE metrics
ADD CONSTRAINT fk_metrics_device
FOREIGN KEY (device_id)
REFERENCES devices(device_id)
ON DELETE CASCADE;

-- ============================================================================
-- 4. COST_CALCULATIONS TABLE (For calculated costs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cost_calculations (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(100) NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    energy_kwh DOUBLE PRECISION NOT NULL,
    average_power_w DOUBLE PRECISION,
    peak_power_w DOUBLE PRECISION,
    cost_total DOUBLE PRECISION NOT NULL,
    cost_energy DOUBLE PRECISION NOT NULL,
    cost_demand DOUBLE PRECISION DEFAULT 0,
    cost_taxes DOUBLE PRECISION DEFAULT 0,
    rate_id VARCHAR(100),
    rate_period VARCHAR(50),
    rate_per_kwh DOUBLE PRECISION,
    carbon_co2_kg DOUBLE PRECISION,
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE cost_calculations IS 'Calculated energy costs and carbon emissions';

-- Convert cost_calculations to hypertable
SELECT create_hypertable(
    'cost_calculations',
    'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Add foreign keys
ALTER TABLE cost_calculations
ADD CONSTRAINT fk_cost_device
FOREIGN KEY (device_id)
REFERENCES devices(device_id)
ON DELETE CASCADE;

ALTER TABLE cost_calculations
ADD CONSTRAINT fk_cost_rate
FOREIGN KEY (rate_id)
REFERENCES rate_schedules(rate_id)
ON DELETE SET NULL;

-- ============================================================================
-- 5. VERIFY HYPERTABLES
-- ============================================================================
-- Show created hypertables
SELECT hypertable_name, num_dimensions, num_chunks
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'public';

-- ============================================================================
-- 6. RECORD MIGRATION
-- ============================================================================
INSERT INTO migration_history (version, description)
VALUES ('002', 'Create hypertables - metrics and cost_calculations')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
DECLARE
    hypertable_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO hypertable_count
    FROM timescaledb_information.hypertables
    WHERE hypertable_schema = 'public';

    RAISE NOTICE '✅ Migration 002_create_hypertables completed successfully';
    RAISE NOTICE 'Hypertables created: %', hypertable_count;
    RAISE NOTICE 'Tables: metrics (7-day chunks), cost_calculations (7-day chunks)';
END $$;
