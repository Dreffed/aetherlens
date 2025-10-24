-- Migration: 003_create_indexes
-- Description: Create indexes for optimized query performance
-- Date: 2025-10-24
-- Author: AetherLens Team

-- ============================================================================
-- 1. METRICS TABLE INDEXES
-- ============================================================================

-- Index for device-based time-series queries (most common pattern)
CREATE INDEX IF NOT EXISTS idx_metrics_device_time
ON metrics (device_id, time DESC);

-- Index for metric type queries
CREATE INDEX IF NOT EXISTS idx_metrics_type_time
ON metrics (metric_type, time DESC);

-- GIN index for JSONB tags (for filtering by room, circuit, etc.)
CREATE INDEX IF NOT EXISTS idx_metrics_tags
ON metrics USING GIN (tags);

-- Partial index for recent data (last 7 days) - frequently accessed
CREATE INDEX IF NOT EXISTS idx_metrics_recent
ON metrics (device_id, time DESC)
WHERE time > NOW() - INTERVAL '7 days';

-- Composite index for device + metric type queries
CREATE INDEX IF NOT EXISTS idx_metrics_device_type_time
ON metrics (device_id, metric_type, time DESC);

-- ============================================================================
-- 2. COST_CALCULATIONS TABLE INDEXES
-- ============================================================================

-- Index for cost queries by device and time
CREATE INDEX IF NOT EXISTS idx_cost_device_time
ON cost_calculations (device_id, time DESC);

-- Index for querying by rate period (peak, off-peak, etc.)
CREATE INDEX IF NOT EXISTS idx_cost_rate_period
ON cost_calculations (rate_period, time DESC);

-- Index for querying by date (for daily summaries)
CREATE INDEX IF NOT EXISTS idx_cost_date
ON cost_calculations (DATE(time), device_id);

-- ============================================================================
-- 3. DEVICES TABLE INDEXES
-- ============================================================================

-- Index for device type queries
CREATE INDEX IF NOT EXISTS idx_devices_type
ON devices(type);

-- GIN index for location queries (finding devices by room, floor, etc.)
CREATE INDEX IF NOT EXISTS idx_devices_location
ON devices USING GIN (location);

-- GIN index for status queries
CREATE INDEX IF NOT EXISTS idx_devices_status
ON devices USING GIN (status);

-- Partial index for online devices only
CREATE INDEX IF NOT EXISTS idx_devices_online
ON devices ((status->>'online'))
WHERE (status->>'online') = 'true';

-- ============================================================================
-- 4. USERS TABLE INDEXES
-- ============================================================================

-- Index for login queries
CREATE INDEX IF NOT EXISTS idx_users_username
ON users(username);

CREATE INDEX IF NOT EXISTS idx_users_email
ON users(email);

-- Partial index for active users only
CREATE INDEX IF NOT EXISTS idx_users_active
ON users(user_id)
WHERE is_active = true;

-- ============================================================================
-- 5. API_TOKENS TABLE INDEXES
-- ============================================================================

-- Index for token lookups
CREATE INDEX IF NOT EXISTS idx_api_tokens_user
ON api_tokens(user_id);

-- Partial index for active tokens only
CREATE INDEX IF NOT EXISTS idx_api_tokens_active
ON api_tokens(token_id)
WHERE is_active = true AND (expires_at IS NULL OR expires_at > NOW());

-- ============================================================================
-- 6. ALERTS TABLE INDEXES
-- ============================================================================

-- Index for user's alerts
CREATE INDEX IF NOT EXISTS idx_alerts_user
ON alerts(user_id);

-- Partial index for enabled alerts only
CREATE INDEX IF NOT EXISTS idx_alerts_enabled
ON alerts(alert_id)
WHERE enabled = true;

-- ============================================================================
-- 7. RATE_SCHEDULES TABLE INDEXES
-- ============================================================================

-- Index for active rate schedules
CREATE INDEX IF NOT EXISTS idx_rate_schedules_active
ON rate_schedules(effective_date, expiry_date)
WHERE is_active = true;

-- Index for provider queries
CREATE INDEX IF NOT EXISTS idx_rate_schedules_provider
ON rate_schedules(provider);

-- ============================================================================
-- 8. PLUGINS TABLE INDEXES
-- ============================================================================

-- Partial index for enabled plugins
CREATE INDEX IF NOT EXISTS idx_plugins_enabled
ON plugins(plugin_id)
WHERE enabled = true;

-- ============================================================================
-- 9. ANALYZE TABLES FOR QUERY PLANNER
-- ============================================================================

ANALYZE metrics;
ANALYZE cost_calculations;
ANALYZE devices;
ANALYZE users;
ANALYZE api_tokens;
ANALYZE alerts;
ANALYZE rate_schedules;
ANALYZE plugins;

-- ============================================================================
-- 10. RECORD MIGRATION
-- ============================================================================
INSERT INTO migration_history (version, description)
VALUES ('003', 'Create indexes for performance optimization')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public';

    RAISE NOTICE '✅ Migration 003_create_indexes completed successfully';
    RAISE NOTICE 'Total indexes in public schema: %', index_count;
    RAISE NOTICE 'Query performance optimized for:';
    RAISE NOTICE '  - Time-series queries (device + time)';
    RAISE NOTICE '  - Recent data access (7-day window)';
    RAISE NOTICE '  - Tag-based filtering (JSONB)';
    RAISE NOTICE '  - Cost analysis queries';
    RAISE NOTICE '  - Active users/tokens/alerts';
END $$;
