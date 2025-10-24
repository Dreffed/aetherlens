-- Sample Data for AetherLens Development
-- This script loads realistic test data for development and testing
-- Date: 2025-10-24

-- ============================================================================
-- 1. SAMPLE USERS
-- ============================================================================

INSERT INTO users (user_id, username, email, password_hash, role, preferences) VALUES
('usr-admin', 'admin', 'admin@aetherlens.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS6n7qQj2', 'admin',
 '{"timezone": "America/Los_Angeles", "currency": "USD", "theme": "dark", "date_format": "YYYY-MM-DD"}'),
('usr-john', 'johndoe', 'john@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS6n7qQj2', 'user',
 '{"timezone": "America/New_York", "currency": "USD", "theme": "light"}')
ON CONFLICT (user_id) DO NOTHING;

-- ============================================================================
-- 2. SAMPLE DEVICES
-- ============================================================================

INSERT INTO devices (device_id, name, type, manufacturer, model, location, capabilities, configuration, status) VALUES
('shelly-office-01', 'Office Desk Plug', 'smart_plug', 'Shelly', 'Plug S',
 '{"room": "office", "floor": 2, "building": "main"}',
 ARRAY['power_monitoring', 'on_off_control', 'energy_metering'],
 '{"ip_address": "192.168.1.100", "polling_interval": 30}',
 '{"online": true, "last_seen": "' || NOW() || '", "error_count": 0}'),

('tp-link-living-room', 'Living Room Lamp', 'smart_plug', 'TP-Link', 'HS110',
 '{"room": "living_room", "floor": 1}',
 ARRAY['power_monitoring', 'on_off_control'],
 '{"ip_address": "192.168.1.101", "polling_interval": 60}',
 '{"online": true, "last_seen": "' || NOW() || '", "error_count": 0}'),

('solar-inverter-01', 'Rooftop Solar Inverter', 'solar_inverter', 'Enphase', 'IQ7+',
 '{"room": "garage", "floor": 1}',
 ARRAY['power_generation', 'energy_metering'],
 '{"ip_address": "192.168.1.102", "polling_interval": 300}',
 '{"online": true, "last_seen": "' || NOW() || '", "error_count": 0}'),

('hvac-main', 'Main HVAC System', 'hvac', 'Nest', 'Learning Thermostat',
 '{"room": "hallway", "floor": 1}',
 ARRAY['power_monitoring', 'temperature_monitoring'],
 '{"ip_address": "192.168.1.103", "polling_interval": 120}',
 '{"online": true, "last_seen": "' || NOW() || '", "error_count": 0}')
ON CONFLICT (device_id) DO NOTHING;

-- ============================================================================
-- 3. SAMPLE RATE SCHEDULES
-- ============================================================================

INSERT INTO rate_schedules (rate_id, provider, plan_name, effective_date, currency, time_zone, rate_structure) VALUES
('pge-tou-summer-2024', 'Pacific Gas & Electric', 'Time-of-Use Summer', '2024-06-01', 'USD', 'America/Los_Angeles',
 '{
   "type": "time_of_use",
   "periods": [
     {"name": "peak", "rate": 0.42, "days": ["monday", "tuesday", "wednesday", "thursday", "friday"], "hours": "16:00-21:00"},
     {"name": "off_peak", "rate": 0.24, "days": ["all"], "hours": "00:00-15:59,21:00-23:59"},
     {"name": "super_off_peak", "rate": 0.12, "days": ["saturday", "sunday"], "hours": "00:00-23:59"}
   ]
 }'),

('flat-rate-test', 'Test Utility', 'Flat Rate Plan', '2024-01-01', 'USD', 'America/Los_Angeles',
 '{
   "type": "flat",
   "periods": [
     {"name": "standard", "rate": 0.25, "days": ["all"], "hours": "00:00-23:59"}
   ]
 }')
ON CONFLICT (rate_id) DO NOTHING;

-- ============================================================================
-- 4. SAMPLE METRICS (Last 7 days, 5-minute intervals)
-- ============================================================================

-- Office plug: Typical office equipment power consumption (100-200W)
INSERT INTO metrics (time, device_id, metric_type, value, unit, tags)
SELECT
    NOW() - (n || ' minutes')::INTERVAL as time,
    'shelly-office-01' as device_id,
    'power' as metric_type,
    100.0 + (random() * 100) as value,
    'watts' as unit,
    '{"room": "office", "device_type": "smart_plug"}'::JSONB as tags
FROM generate_series(0, 7 * 24 * 60 / 5) as n;

-- Living room lamp: Variable usage (0-60W, simulating on/off patterns)
INSERT INTO metrics (time, device_id, metric_type, value, unit)
SELECT
    NOW() - (n || ' minutes')::INTERVAL,
    'tp-link-living-room',
    'power',
    CASE
        WHEN EXTRACT(HOUR FROM NOW() - (n || ' minutes')::INTERVAL) BETWEEN 6 AND 23
        THEN random() * 60
        ELSE 0
    END,
    'watts'
FROM generate_series(0, 7 * 24 * 60 / 5) as n;

-- Solar inverter: Daytime generation pattern (0-3000W)
INSERT INTO metrics (time, device_id, metric_type, value, unit)
SELECT
    NOW() - (n || ' minutes')::INTERVAL,
    'solar-inverter-01',
    'power',
    CASE
        WHEN EXTRACT(HOUR FROM NOW() - (n || ' minutes')::INTERVAL) BETWEEN 8 AND 18
        THEN 1500 + (random() * 1500)
        ELSE random() * 10
    END,
    'watts'
FROM generate_series(0, 7 * 24 * 60 / 5) as n;

-- ============================================================================
-- 5. SAMPLE API TOKENS
-- ============================================================================

INSERT INTO api_tokens (token_id, user_id, token_hash, name, permissions, expires_at) VALUES
('tok-home-assistant', 'usr-admin', '$2b$12$sample_token_hash_here', 'Home Assistant Integration',
 ARRAY['read:metrics', 'read:devices', 'write:metrics'],
 NOW() + INTERVAL '1 year')
ON CONFLICT (token_id) DO NOTHING;

-- ============================================================================
-- 6. SAMPLE ALERT
-- ============================================================================

INSERT INTO alerts (alert_id, user_id, name, enabled, conditions, actions) VALUES
('alert-high-power', 'usr-admin', 'High Office Power Consumption', true,
 '{
   "type": "threshold",
   "metric": "power",
   "device_id": "shelly-office-01",
   "operator": "greater_than",
   "threshold": 500,
   "duration_seconds": 300
 }',
 '{
   "actions": [
     {"type": "notification", "channels": ["email"], "message": "Office consuming >500W for 5 minutes"}
   ]
 }')
ON CONFLICT (alert_id) DO NOTHING;

-- ============================================================================
-- 7. SAMPLE PLUGIN
-- ============================================================================

INSERT INTO plugins (plugin_id, name, version, enabled, configuration) VALUES
('plugin-shelly', 'Shelly Devices Plugin', '1.0.0', true,
 '{"devices": ["shelly-office-01"], "polling_interval": 30}'),
('plugin-home-assistant', 'Home Assistant Plugin', '1.0.0', false,
 '{"url": "http://homeassistant.local:8123", "entities": []}')
ON CONFLICT (plugin_id) DO NOTHING;

-- ============================================================================
-- 8. REFRESH CONTINUOUS AGGREGATES (force calculation for sample data)
-- ============================================================================

-- Note: In production, these refresh automatically via policies
-- For testing, we manually refresh to populate the aggregates immediately
CALL refresh_continuous_aggregate('metrics_hourly', NOW() - INTERVAL '7 days', NOW());
CALL refresh_continuous_aggregate('metrics_daily', NOW() - INTERVAL '7 days', NOW());

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
DECLARE
    device_count INTEGER;
    metric_count INTEGER;
    user_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO device_count FROM devices;
    SELECT COUNT(*) INTO metric_count FROM metrics;
    SELECT COUNT(*) INTO user_count FROM users;

    RAISE NOTICE '✅ Sample data loaded successfully';
    RAISE NOTICE 'Users: %', user_count;
    RAISE NOTICE 'Devices: %', device_count;
    RAISE NOTICE 'Metrics: ~%', metric_count;
    RAISE NOTICE 'Rate Schedules: 2';
    RAISE NOTICE 'Continuous aggregates refreshed';
    RAISE NOTICE '';
    RAISE NOTICE 'Test credentials: admin / password (hash in DB)';
    RAISE NOTICE 'Sample devices ready for testing';
END $$;
