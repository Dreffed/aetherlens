-- AetherLens Database Initialization
-- This script runs automatically when the database is first created
-- File: migrations/init/01-enable-timescaledb.sql

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Verify TimescaleDB is installed
SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';

-- Set timezone to UTC for consistency
SET timezone = 'UTC';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB extension enabled successfully';
    RAISE NOTICE 'Database initialized for AetherLens';
END $$;
