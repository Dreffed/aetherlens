-- Migration: 005_compression_policies
-- Description: Enable compression for time-series data
-- Date: 2025-10-24
-- Author: AetherLens Team

-- ============================================================================
-- 1. ENABLE COMPRESSION ON METRICS TABLE
-- ============================================================================

-- Configure compression settings
ALTER TABLE metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id, metric_type',
    timescaledb.compress_orderby = 'time DESC'
);

-- Add compression policy (compress chunks older than 7 days)
SELECT add_compression_policy('metrics', INTERVAL '7 days');

COMMENT ON TABLE metrics IS 'Time-series metrics (compressed after 7 days)';

-- ============================================================================
-- 2. ENABLE COMPRESSION ON COST_CALCULATIONS TABLE
-- ============================================================================

-- Configure compression settings
ALTER TABLE cost_calculations SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id',
    timescaledb.compress_orderby = 'time DESC'
);

-- Add compression policy (compress chunks older than 7 days)
SELECT add_compression_policy('cost_calculations', INTERVAL '7 days');

COMMENT ON TABLE cost_calculations IS 'Cost calculations (compressed after 7 days)';

-- ============================================================================
-- 3. VERIFY COMPRESSION SETTINGS
-- ============================================================================

-- Show compression settings
SELECT
    hypertable_name,
    compression_enabled,
    compress_segmentby,
    compress_orderby
FROM timescaledb_information.compression_settings
WHERE hypertable_schema = 'public';

-- Show compression policies
SELECT
    hypertable_name,
    older_than
FROM timescaledb_information.jobs j
JOIN timescaledb_information.hypertables h ON j.hypertable_name = h.hypertable_name
WHERE proc_name = 'policy_compression'
  AND h.hypertable_schema = 'public';

-- ============================================================================
-- 4. RECORD MIGRATION
-- ============================================================================
INSERT INTO migration_history (version, description)
VALUES ('005', 'Enable compression policies - compress data older than 7 days')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
DECLARE
    compression_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO compression_count
    FROM timescaledb_information.compression_settings
    WHERE hypertable_schema = 'public'
      AND compression_enabled = TRUE;

    RAISE NOTICE '✅ Migration 005_compression_policies completed successfully';
    RAISE NOTICE 'Compression enabled on % hypertables', compression_count;
    RAISE NOTICE 'Compression settings:';
    RAISE NOTICE '  - metrics: segment by (device_id, metric_type), order by time DESC';
    RAISE NOTICE '  - cost_calculations: segment by device_id, order by time DESC';
    RAISE NOTICE '  - Compress chunks older than: 7 days';
    RAISE NOTICE '  - Expected compression ratio: >70%%';
    RAISE NOTICE 'Compression will run automatically via background jobs';
END $$;
