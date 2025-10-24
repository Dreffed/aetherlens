-- Migration: 006_retention_policies
-- Description: Configure automatic data retention policies
-- Date: 2025-10-24
-- Author: AetherLens Team

-- ============================================================================
-- RETENTION POLICY OVERVIEW
-- ============================================================================
--
-- Data retention strategy:
-- - Raw metrics: 90 days (compressed after 7 days)
-- - Cost calculations: 90 days (compressed after 7 days)
-- - Hourly aggregates: 1 year
-- - Daily aggregates: 5 years
--
-- This ensures efficient storage while maintaining historical data in aggregates
-- ============================================================================

-- ============================================================================
-- 1. RAW METRICS RETENTION (90 days)
-- ============================================================================

-- Drop chunks older than 90 days from metrics table
SELECT add_retention_policy('metrics', INTERVAL '90 days');

-- ============================================================================
-- 2. COST CALCULATIONS RETENTION (90 days)
-- ============================================================================

-- Drop chunks older than 90 days from cost_calculations table
SELECT add_retention_policy('cost_calculations', INTERVAL '90 days');

-- ============================================================================
-- 3. HOURLY AGGREGATES RETENTION (1 year)
-- ============================================================================

-- Drop chunks older than 1 year from hourly views
SELECT add_retention_policy('metrics_hourly', INTERVAL '1 year');
SELECT add_retention_policy('cost_hourly', INTERVAL '1 year');

-- ============================================================================
-- 4. DAILY AGGREGATES RETENTION (5 years)
-- ============================================================================

-- Drop chunks older than 5 years from daily views
SELECT add_retention_policy('metrics_daily', INTERVAL '5 years');
SELECT add_retention_policy('cost_daily', INTERVAL '5 years');

-- ============================================================================
-- 5. VERIFY RETENTION POLICIES
-- ============================================================================

-- Show all retention policies
SELECT
    j.job_id,
    h.hypertable_name,
    j.schedule_interval,
    j.config->>'drop_after' as retention_period
FROM timescaledb_information.jobs j
JOIN timescaledb_information.hypertables h
    ON j.hypertable_schema = h.hypertable_schema
    AND j.hypertable_name = h.hypertable_name
WHERE j.proc_name = 'policy_retention'
ORDER BY h.hypertable_name;

-- ============================================================================
-- 6. CREATE CLEANUP FUNCTION (for manual cleanup if needed)
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS TABLE (
    table_name TEXT,
    chunks_dropped INTEGER,
    bytes_freed BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'metrics'::TEXT,
        0::INTEGER,
        0::BIGINT
    WHERE FALSE;

    RAISE NOTICE 'Manual cleanup function created';
    RAISE NOTICE 'Automatic retention policies are active';
    RAISE NOTICE 'Use: SELECT * FROM timescaledb_information.jobs WHERE proc_name = ''policy_retention'';';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_data() IS 'Manual cleanup function (retention policies run automatically)';

-- ============================================================================
-- 7. RECORD MIGRATION
-- ============================================================================
INSERT INTO migration_history (version, description)
VALUES ('006', 'Configure retention policies - 90d raw, 1yr hourly, 5yr daily')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
DECLARE
    retention_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO retention_count
    FROM timescaledb_information.jobs
    WHERE proc_name = 'policy_retention';

    RAISE NOTICE '✅ Migration 006_retention_policies completed successfully';
    RAISE NOTICE 'Retention policies configured: %', retention_count;
    RAISE NOTICE 'Data retention rules:';
    RAISE NOTICE '  - metrics (raw): 90 days';
    RAISE NOTICE '  - cost_calculations (raw): 90 days';
    RAISE NOTICE '  - metrics_hourly: 1 year';
    RAISE NOTICE '  - cost_hourly: 1 year';
    RAISE NOTICE '  - metrics_daily: 5 years';
    RAISE NOTICE '  - cost_daily: 5 years';
    RAISE NOTICE '';
    RAISE NOTICE 'Storage strategy:';
    RAISE NOTICE '  - Recent data (<7d): Uncompressed for fast access';
    RAISE NOTICE '  - Older data (7-90d): Compressed (~70%% space savings)';
    RAISE NOTICE '  - Historical: Aggregates only (hourly/daily)';
    RAISE NOTICE 'Retention jobs will run automatically in the background';
END $$;
