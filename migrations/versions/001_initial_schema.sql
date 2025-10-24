-- Migration: 001_initial_schema
-- Description: Create core database tables for AetherLens
-- Date: 2025-10-24
-- Author: AetherLens Team

-- ============================================================================
-- 1. DEVICES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    location JSONB NOT NULL DEFAULT '{}',
    capabilities TEXT[] DEFAULT '{}',
    configuration JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    status JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE devices IS 'Registry of all monitored devices and their configurations';
COMMENT ON COLUMN devices.device_id IS 'Unique identifier for the device';
COMMENT ON COLUMN devices.location IS 'Physical location data (room, floor, building, coordinates)';
COMMENT ON COLUMN devices.capabilities IS 'Array of device capabilities (power_monitoring, on_off_control, etc.)';
COMMENT ON COLUMN devices.configuration IS 'Device-specific configuration (IP, polling interval, auth, etc.)';
COMMENT ON COLUMN devices.status IS 'Current device status (online, last_seen, error_count, etc.)';

-- ============================================================================
-- 2. USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

COMMENT ON TABLE users IS 'User accounts and authentication';
COMMENT ON COLUMN users.role IS 'User role: admin, user, viewer';
COMMENT ON COLUMN users.preferences IS 'User preferences (timezone, currency, dashboard layout, notifications)';

-- ============================================================================
-- 3. API_TOKENS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_tokens (
    token_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    permissions TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

COMMENT ON TABLE api_tokens IS 'API tokens for programmatic access';
COMMENT ON COLUMN api_tokens.permissions IS 'Array of permissions (read:metrics, write:devices, etc.)';

-- ============================================================================
-- 4. RATE_SCHEDULES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS rate_schedules (
    rate_id VARCHAR(100) PRIMARY KEY,
    provider VARCHAR(100) NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    time_zone VARCHAR(50) NOT NULL,
    rate_structure JSONB NOT NULL,
    fixed_charges JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

COMMENT ON TABLE rate_schedules IS 'Electricity rate schedules (TOU, tiered, fixed)';
COMMENT ON COLUMN rate_schedules.rate_structure IS 'Rate configuration (type, periods, rates)';
COMMENT ON COLUMN rate_schedules.fixed_charges IS 'Monthly/daily fixed charges';

-- ============================================================================
-- 5. ALERTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    conditions JSONB NOT NULL,
    actions JSONB NOT NULL,
    schedule JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP,
    trigger_count INTEGER DEFAULT 0
);

COMMENT ON TABLE alerts IS 'Alert rules and automation configurations';
COMMENT ON COLUMN alerts.conditions IS 'Alert trigger conditions (type, threshold, duration)';
COMMENT ON COLUMN alerts.actions IS 'Actions to take when triggered (notification, automation)';

-- ============================================================================
-- 6. PLUGINS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS plugins (
    plugin_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    enabled BOOLEAN DEFAULT false,
    configuration JSONB DEFAULT '{}',
    status JSONB DEFAULT '{}',
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_run TIMESTAMP,
    error_count INTEGER DEFAULT 0
);

COMMENT ON TABLE plugins IS 'Installed plugins and their status';
COMMENT ON COLUMN plugins.configuration IS 'Plugin-specific configuration';
COMMENT ON COLUMN plugins.status IS 'Plugin health status (online, error_message, metrics_collected)';

-- ============================================================================
-- 7. MIGRATION_HISTORY TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS migration_history (
    migration_id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100) DEFAULT 'system'
);

COMMENT ON TABLE migration_history IS 'Track database schema migrations';

-- Record this migration
INSERT INTO migration_history (version, description)
VALUES ('001', 'Initial schema - core tables (devices, users, api_tokens, rate_schedules, alerts, plugins)')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 001_initial_schema completed successfully';
    RAISE NOTICE 'Tables created: devices, users, api_tokens, rate_schedules, alerts, plugins, migration_history';
END $$;
