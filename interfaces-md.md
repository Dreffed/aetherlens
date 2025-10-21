# API & Plugin Interface Specification

## Overview

This document defines the complete API surface and plugin architecture for AetherLens Home Edition, including REST APIs, GraphQL schemas, WebSocket protocols, and the plugin development interface.

## Table of Contents

1. [REST API](#rest-api)
2. [GraphQL API](#graphql-api)
3. [WebSocket API](#websocket-api)
4. [Plugin Architecture](#plugin-architecture)
5. [Plugin SDK](#plugin-sdk)
6. [Authentication & Authorization](#authentication--authorization)
7. [Rate Limiting & Quotas](#rate-limiting--quotas)
8. [Error Handling](#error-handling)

## REST API

### Base Configuration

```yaml
openapi: 3.0.3
info:
  title: AetherLens Home Edition API
  version: 1.0.0
  description: Home energy monitoring and cost optimization platform
servers:
  - url: http://localhost:8080/api/v1
  - url: https://aetherlens.local/api/v1
```

### Core Endpoints

#### Metrics

```yaml
# GET /metrics/current
# Get current metrics for all devices
GET /api/v1/metrics/current
Response: 200 OK
{
  "timestamp": "2024-01-15T10:30:00Z",
  "devices": [
    {
      "device_id": "shelly-plug-office-01",
      "metrics": {
        "power": 125.4,
        "voltage": 120.1,
        "current": 1.04
      },
      "unit": "watts"
    }
  ]
}

# GET /metrics/history
# Get historical metrics with filtering
GET /api/v1/metrics/history?device_id=shelly-plug-office-01&start=2024-01-01&end=2024-01-15&resolution=1h
Response: 200 OK
{
  "device_id": "shelly-plug-office-01",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-15T23:59:59Z",
    "resolution": "1h"
  },
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "value": 125.4,
      "min": 0,
      "max": 350.2,
      "avg": 125.4
    }
  ]
}

# POST /metrics
# Submit metrics (for external collectors)
POST /api/v1/metrics
Content-Type: application/json
{
  "device_id": "custom-sensor-01",
  "timestamp": "2024-01-15T10:30:00Z",
  "metrics": {
    "temperature": 22.5,
    "humidity": 45.2
  }
}
Response: 201 Created
```

#### Devices

```yaml
# GET /devices
# List all devices
GET /api/v1/devices
Response: 200 OK
{
  "devices": [
    {
      "device_id": "shelly-plug-office-01",
      "name": "Office Desk Plug",
      "type": "smart_plug",
      "status": "online",
      "last_seen": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 42
}

# GET /devices/{id}
# Get device details
GET /api/v1/devices/shelly-plug-office-01
Response: 200 OK
{
  "device_id": "shelly-plug-office-01",
  "name": "Office Desk Plug",
  "type": "smart_plug",
  "manufacturer": "Shelly",
  "model": "Plug S",
  "location": {
    "room": "office",
    "floor": 2
  },
  "capabilities": ["power_monitoring", "on_off_control"],
  "configuration": {...},
  "status": {
    "online": true,
    "last_seen": "2024-01-15T10:30:00Z"
  }
}

# POST /devices
# Register new device
POST /api/v1/devices
Content-Type: application/json
{
  "name": "Living Room Lamp",
  "type": "smart_plug",
  "plugin": "shelly",
  "configuration": {
    "ip_address": "192.168.1.101"
  }
}
Response: 201 Created

# PUT /devices/{id}
# Update device configuration
PUT /api/v1/devices/shelly-plug-office-01
Content-Type: application/json
{
  "name": "Updated Name",
  "location": {
    "room": "bedroom"
  }
}
Response: 200 OK

# DELETE /devices/{id}
# Remove device
DELETE /api/v1/devices/shelly-plug-office-01
Response: 204 No Content
```

#### Cost & Energy

```yaml
# GET /costs/current
# Get current cost calculations
GET /api/v1/costs/current
Response: 200 OK
{
  "timestamp": "2024-01-15T10:30:00Z",
  "total_power_w": 1234.5,
  "cost_per_hour": 0.42,
  "currency": "USD",
  "rate_period": "peak",
  "devices": [
    {
      "device_id": "shelly-plug-office-01",
      "power_w": 125.4,
      "cost_per_hour": 0.053
    }
  ]
}

# GET /costs/summary
# Get cost summary for period
GET /api/v1/costs/summary?period=month&date=2024-01
Response: 200 OK
{
  "period": "2024-01",
  "total_kwh": 324.5,
  "total_cost": 89.43,
  "currency": "USD",
  "breakdown": {
    "peak": 45.20,
    "off_peak": 34.23,
    "super_off_peak": 10.00
  },
  "daily_average": 2.98
}

# GET /energy/rates
# Get current energy rate configuration
GET /api/v1/energy/rates
Response: 200 OK
{
  "provider": "Pacific Gas & Electric",
  "plan": "Time-of-Use",
  "current_rate": 0.42,
  "current_period": "peak",
  "periods": [...]
}
```

#### Plugins

```yaml
# GET /plugins
# List installed plugins
GET /api/v1/plugins
Response: 200 OK
{
  "plugins": [
    {
      "id": "shelly",
      "name": "Shelly Smart Devices",
      "version": "1.2.0",
      "status": "active",
      "capabilities": ["metrics.collect", "device.control"]
    }
  ]
}

# POST /plugins/{id}/reload
# Reload plugin configuration
POST /api/v1/plugins/shelly/reload
Response: 200 OK
{
  "status": "reloaded",
  "message": "Plugin reloaded successfully"
}
```

### Prometheus Metrics Endpoint

```yaml
# GET /metrics (Prometheus format)
GET /metrics
Response: 200 OK
# HELP aetherlens_power_watts Current power consumption in watts
# TYPE aetherlens_power_watts gauge
aetherlens_power_watts{device="shelly-plug-office-01",room="office"} 125.4
aetherlens_power_watts{device="emporia-vue-main",circuit="1"} 234.5

# HELP aetherlens_energy_kwh_total Total energy consumption
# TYPE aetherlens_energy_kwh_total counter
aetherlens_energy_kwh_total{device="shelly-plug-office-01"} 1234.5
```

## GraphQL API

### Schema Definition

```graphql
type Query {
  # Device queries
  devices(filter: DeviceFilter): [Device!]!
  device(id: ID!): Device
  
  # Metrics queries
  currentMetrics(deviceId: ID): MetricsSnapshot!
  historicalMetrics(
    deviceId: ID!
    start: DateTime!
    end: DateTime!
    resolution: Resolution
  ): TimeSeriesData!
  
  # Cost queries
  currentCosts: CostSnapshot!
  costSummary(period: Period!, date: Date): CostSummary!
  
  # Energy rates
  energyRates: EnergyRateConfig!
  
  # Alerts
  alerts(active: Boolean): [Alert!]!
}

type Mutation {
  # Device management
  createDevice(input: CreateDeviceInput!): Device!
  updateDevice(id: ID!, input: UpdateDeviceInput!): Device!
  deleteDevice(id: ID!): Boolean!
  
  # Device control
  controlDevice(id: ID!, action: DeviceAction!): ControlResult!
  
  # Configuration
  updateEnergyRates(input: EnergyRateInput!): EnergyRateConfig!
  
  # Alerts
  createAlert(input: CreateAlertInput!): Alert!
  updateAlert(id: ID!, input: UpdateAlertInput!): Alert!
  deleteAlert(id: ID!): Boolean!
}

type Subscription {
  # Real-time metrics
  metricsUpdated(deviceId: ID): MetricsUpdate!
  
  # Device status
  deviceStatusChanged: DeviceStatus!
  
  # Alerts
  alertTriggered: AlertEvent!
  
  # Cost updates
  costUpdated: CostUpdate!
}

# Core Types
type Device {
  id: ID!
  name: String!
  type: DeviceType!
  manufacturer: String
  model: String
  location: Location
  status: DeviceStatus!
  capabilities: [String!]!
  currentMetrics: MetricsSnapshot
  configuration: JSON
  createdAt: DateTime!
  updatedAt: DateTime!
}

type MetricsSnapshot {
  timestamp: DateTime!
  power: Float
  energy: Float
  voltage: Float
  current: Float
  frequency: Float
  powerFactor: Float
  temperature: Float
  custom: JSON
}

type CostSnapshot {
  timestamp: DateTime!
  totalPower: Float!
  costPerHour: Float!
  currency: String!
  ratePeriod: String!
  devices: [DeviceCost!]!
}

enum DeviceType {
  SMART_PLUG
  ENERGY_MONITOR
  SOLAR_INVERTER
  BATTERY
  EV_CHARGER
  THERMOSTAT
  CUSTOM
}

enum Resolution {
  RAW
  MINUTE
  FIVE_MINUTES
  HOUR
  DAY
  WEEK
  MONTH
}
```

## WebSocket API

### Connection

```javascript
// WebSocket connection endpoint
ws://localhost:8080/api/v1/ws

// Authentication via query parameter or header
ws://localhost:8080/api/v1/ws?token=<jwt_token>
```

### Message Protocol

```typescript
// Client to Server Messages
interface ClientMessage {
  type: 'subscribe' | 'unsubscribe' | 'ping';
  id?: string;  // Request ID for correlation
  topic?: string;  // Subscription topic
  filters?: Record<string, any>;
}

// Server to Client Messages
interface ServerMessage {
  type: 'data' | 'error' | 'pong' | 'subscribed' | 'unsubscribed';
  id?: string;  // Correlation ID
  topic?: string;
  data?: any;
  error?: string;
  timestamp: string;
}

// Subscription Topics
enum Topics {
  METRICS = 'metrics.*',  // metrics.{device_id} or metrics.all
  COSTS = 'costs',
  ALERTS = 'alerts',
  DEVICES = 'devices.*',  // devices.status, devices.config
  SYSTEM = 'system.*'  // system.health, system.performance
}
```

### Example WebSocket Flow

```javascript
// Client subscribes to metrics
{
  "type": "subscribe",
  "id": "req-001",
  "topic": "metrics.shelly-plug-office-01"
}

// Server confirms subscription
{
  "type": "subscribed",
  "id": "req-001",
  "topic": "metrics.shelly-plug-office-01"
}

// Server sends real-time data
{
  "type": "data",
  "topic": "metrics.shelly-plug-office-01",
  "data": {
    "timestamp": "2024-01-15T10:30:00Z",
    "power": 125.4,
    "energy": 0.0627
  }
}
```

## Plugin Architecture

### Plugin gRPC Service Definition

```protobuf
syntax = "proto3";
package aetherlens.plugin.v1;

service PluginService {
  // Lifecycle management
  rpc GetInfo(Empty) returns (PluginInfo);
  rpc Configure(ConfigRequest) returns (ConfigResponse);
  rpc Start(StartRequest) returns (StartResponse);
  rpc Stop(StopRequest) returns (StopResponse);
  rpc GetHealth(HealthRequest) returns (HealthResponse);
  
  // Metrics collection
  rpc CollectMetrics(CollectRequest) returns (stream Metric);
  rpc GetCapabilities(Empty) returns (Capabilities);
  
  // Device management
  rpc DiscoverDevices(DiscoverRequest) returns (stream Device);
  rpc ControlDevice(ControlRequest) returns (ControlResponse);
  
  // Configuration validation
  rpc ValidateConfig(ValidateRequest) returns (ValidateResponse);
}

// Core Messages
message PluginInfo {
  string id = 1;
  string name = 2;
  string version = 3;
  string author = 4;
  string description = 5;
  repeated string capabilities = 6;
}

message Metric {
  string device_id = 1;
  int64 timestamp = 2;
  string metric_type = 3;
  double value = 4;
  string unit = 5;
  map<string, string> tags = 6;
  map<string, string> metadata = 7;
}

message Device {
  string device_id = 1;
  string name = 2;
  string type = 3;
  string manufacturer = 4;
  string model = 5;
  map<string, string> properties = 6;
  repeated string capabilities = 7;
}

message HealthResponse {
  enum Status {
    UNKNOWN = 0;
    HEALTHY = 1;
    DEGRADED = 2;
    UNHEALTHY = 3;
  }
  Status status = 1;
  string message = 2;
  map<string, string> details = 3;
}
```

### Plugin Manifest

```yaml
# plugin.yaml
id: shelly
name: Shelly Smart Devices
version: 1.2.0
author: AetherLens Community
description: Integration for Shelly smart plugs and energy monitors
homepage: https://github.com/aetherlens/plugin-shelly
license: MIT

runtime:
  type: python  # python, go, nodejs, binary
  version: "3.11"
  entrypoint: shelly_plugin.py

capabilities:
  - metrics.collect
  - device.discover
  - device.control
  - config.validate

requirements:
  core_version: ">=1.0.0"
  dependencies:
    - aiohttp>=3.8
    - pydantic>=2.0

configuration:
  schema:
    type: object
    required: [devices]
    properties:
      devices:
        type: array
        items:
          type: object
          required: [ip_address]
          properties:
            ip_address:
              type: string
              format: ipv4
            name:
              type: string
            username:
              type: string
            password:
              type: string
              secret: true
      poll_interval:
        type: integer
        default: 30
        minimum: 10
        maximum: 3600

metrics:
  - name: power
    type: gauge
    unit: watts
    description: Current power consumption
  - name: energy
    type: counter
    unit: kWh
    description: Total energy consumption
  - name: voltage
    type: gauge
    unit: volts
    description: Current voltage
  - name: current
    type: gauge
    unit: amperes
    description: Current draw

permissions:
  network:
    - local  # Can access local network
  system:
    - none  # No system access needed
```

## Plugin SDK

### Python SDK

```python
# aetherlens_sdk/plugin.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class Metric:
    device_id: str
    metric_type: str
    value: float
    unit: str
    timestamp: Optional[float] = None
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None

@dataclass
class Device:
    device_id: str
    name: str
    type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    properties: Dict[str, Any] = None
    capabilities: List[str] = None

class BasePlugin(ABC):
    """Base class for all AetherLens plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self.get_logger()
        
    @abstractmethod
    async def collect_metrics(self) -> List[Metric]:
        """Collect metrics from devices"""
        pass
    
    @abstractmethod
    async def discover_devices(self) -> List[Device]:
        """Discover available devices"""
        pass
    
    async def control_device(self, device_id: str, action: str, params: Dict) -> Dict:
        """Control a device (optional)"""
        raise NotImplementedError("Device control not supported")
    
    def validate_config(self) -> bool:
        """Validate plugin configuration"""
        return True
    
    def get_capabilities(self) -> List[str]:
        """Return plugin capabilities"""
        return ["metrics.collect"]
    
    def get_health(self) -> Dict:
        """Return plugin health status"""
        return {
            "status": "healthy",
            "message": "Plugin is running"
        }

# Example Plugin Implementation
class ShellyPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.devices = config.get('devices', [])
        self.poll_interval = config.get('poll_interval', 30)
    
    async def collect_metrics(self) -> List[Metric]:
        metrics = []
        for device in self.devices:
            data = await self._fetch_device_data(device['ip_address'])
            metrics.extend([
                Metric(
                    device_id=self._get_device_id(device),
                    metric_type='power',
                    value=data['power'],
                    unit='watts',
                    tags={'room': device.get('room', 'unknown')}
                ),
                Metric(
                    device_id=self._get_device_id(device),
                    metric_type='energy',
                    value=data['total'],
                    unit='kWh'
                )
            ])
        return metrics
    
    async def discover_devices(self) -> List[Device]:
        # Implement mDNS discovery
        devices = []
        # ... discovery logic ...
        return devices
    
    async def control_device(self, device_id: str, action: str, params: Dict) -> Dict:
        if action == 'turn_on':
            return await self._set_relay(device_id, True)
        elif action == 'turn_off':
            return await self._set_relay(device_id, False)
        else:
            raise ValueError(f"Unknown action: {action}")
```

### Go SDK

```go
// sdk/plugin.go
package sdk

import (
    "context"
    "time"
)

type Metric struct {
    DeviceID   string            `json:"device_id"`
    MetricType string            `json:"metric_type"`
    Value      float64           `json:"value"`
    Unit       string            `json:"unit"`
    Timestamp  time.Time         `json:"timestamp"`
    Tags       map[string]string `json:"tags,omitempty"`
    Metadata   map[string]any    `json:"metadata,omitempty"`
}

type Device struct {
    DeviceID     string            `json:"device_id"`
    Name         string            `json:"name"`
    Type         string            `json:"type"`
    Manufacturer string            `json:"manufacturer,omitempty"`
    Model        string            `json:"model,omitempty"`
    Properties   map[string]any    `json:"properties,omitempty"`
    Capabilities []string          `json:"capabilities,omitempty"`
}

type Plugin interface {
    // Lifecycle
    Configure(config map[string]any) error
    Start(ctx context.Context) error
    Stop(ctx context.Context) error
    
    // Core functionality
    CollectMetrics(ctx context.Context) ([]Metric, error)
    DiscoverDevices(ctx context.Context) ([]Device, error)
    ControlDevice(ctx context.Context, deviceID, action string, params map[string]any) (map[string]any, error)
    
    // Metadata
    GetCapabilities() []string
    GetHealth() map[string]any
    ValidateConfig() error
}

// BasePlugin provides default implementations
type BasePlugin struct {
    Config map[string]any
}

func (p *BasePlugin) Configure(config map[string]any) error {
    p.Config = config
    return nil
}

func (p *BasePlugin) GetCapabilities() []string {
    return []string{"metrics.collect"}
}

func (p *BasePlugin) GetHealth() map[string]any {
    return map[string]any{
        "status":  "healthy",
        "message": "Plugin is running",
    }
}
```

### JavaScript/TypeScript SDK

```typescript
// sdk/plugin.ts
export interface Metric {
  deviceId: string;
  metricType: string;
  value: number;
  unit: string;
  timestamp?: Date;
  tags?: Record<string, string>;
  metadata?: Record<string, any>;
}

export interface Device {
  deviceId: string;
  name: string;
  type: string;
  manufacturer?: string;
  model?: string;
  properties?: Record<string, any>;
  capabilities?: string[];
}

export abstract class BasePlugin {
  protected config: Record<string, any>;
  
  constructor(config: Record<string, any>) {
    this.config = config;
  }
  
  abstract collectMetrics(): Promise<Metric[]>;
  abstract discoverDevices(): Promise<Device[]>;
  
  async controlDevice(deviceId: string, action: string, params: Record<string, any>): Promise<any> {
    throw new Error("Device control not supported");
  }
  
  validateConfig(): boolean {
    return true;
  }
  
  getCapabilities(): string[] {
    return ["metrics.collect"];
  }
  
  getHealth(): Record<string, any> {
    return {
      status: "healthy",
      message: "Plugin is running"
    };
  }
}

// Example implementation
export class ShellyPlugin extends BasePlugin {
  private devices: any[];
  
  constructor(config: Record<string, any>) {
    super(config);
    this.devices = config.devices || [];
  }
  
  async collectMetrics(): Promise<Metric[]> {
    const metrics: Metric[] = [];
    
    for (const device of this.devices) {
      const data = await this.fetchDeviceData(device.ipAddress);
      metrics.push({
        deviceId: this.getDeviceId(device),
        metricType: 'power',
        value: data.power,
        unit: 'watts',
        tags: { room: device.room || 'unknown' }
      });
    }
    
    return metrics;
  }
  
  async discoverDevices(): Promise<Device[]> {
    // Implement discovery logic
    return [];
  }
  
  private async fetchDeviceData(ip: string): Promise<any> {
    // Fetch data from device
    const response = await fetch(`http://${ip}/status`);
    return response.json();
  }
  
  private getDeviceId(device: any): string {
    return `shelly-${device.ipAddress.replace(/\./g, '-')}`;
  }
}
```

## Authentication & Authorization

### API Key Authentication

```yaml
# HTTP Header
Authorization: Bearer <api_key>

# Query Parameter (WebSocket)
?token=<api_key>
```

### JWT Token Structure

```json
{
  "sub": "user-001",
  "iat": 1704067200,
  "exp": 1704153600,
  "scope": ["read:metrics", "write:devices", "control:devices"],
  "type": "access_token"
}
```

### Permission Scopes

```yaml
# Read permissions
read:metrics     # Read metric data
read:devices     # Read device information
read:costs       # Read cost calculations
read:config      # Read configuration

# Write permissions
write:devices    # Create/update/delete devices
write:config     # Modify configuration
write:alerts     # Manage alerts

# Control permissions
control:devices  # Control device state
control:plugins  # Manage plugins

# Admin permissions
admin:users      # Manage users
admin:system     # System administration
```

### Role-Based Access Control

```yaml
roles:
  viewer:
    - read:metrics
    - read:devices
    - read:costs
    
  operator:
    - read:*
    - control:devices
    
  admin:
    - read:*
    - write:*
    - control:*
    - admin:*
```

## Rate Limiting & Quotas

### Default Limits

```yaml
rate_limits:
  anonymous:
    requests_per_minute: 10
    requests_per_hour: 100
    
  authenticated:
    requests_per_minute: 60
    requests_per_hour: 1000
    
  admin:
    requests_per_minute: 120
    requests_per_hour: 5000

quotas:
  metrics:
    points_per_day: 1000000
    retention_days: 90
    
  devices:
    max_devices: 100
    max_plugins: 20
```

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1704067200
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Device with ID 'shelly-plug-office-01' not found",
    "details": {
      "device_id": "shelly-plug-office-01",
      "suggestion": "Check device ID or use device discovery"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req-abc123"
  }
}
```

### Standard Error Codes

```yaml
# 4xx Client Errors
BAD_REQUEST: Invalid request format
UNAUTHORIZED: Authentication required
FORBIDDEN: Insufficient permissions
NOT_FOUND: Resource not found
CONFLICT: Resource already exists
RATE_LIMITED: Too many requests
VALIDATION_ERROR: Input validation failed

# 5xx Server Errors
INTERNAL_ERROR: Internal server error
SERVICE_UNAVAILABLE: Service temporarily unavailable
PLUGIN_ERROR: Plugin execution failed
DATABASE_ERROR: Database operation failed
TIMEOUT: Request timeout
```

### Plugin Error Handling

```python
class PluginError(Exception):
    """Base exception for plugin errors"""
    pass

class DeviceNotFoundError(PluginError):
    """Device not found"""
    pass

class DeviceOfflineError(PluginError):
    """Device is offline"""
    pass

class ConfigurationError(PluginError):
    """Invalid plugin configuration"""
    pass

# Usage in plugin
async def collect_metrics(self):
    try:
        data = await self.fetch_device_data()
        return self.parse_metrics(data)
    except ConnectionError as e:
        raise DeviceOfflineError(f"Cannot connect to device: {e}")
    except KeyError as e:
        raise ConfigurationError(f"Missing configuration: {e}")
```

## Plugin Communication Patterns

### Request-Response Pattern

```python
# Plugin requests data from core
response = await self.core.request('storage.query', {
    'metric': 'power',
    'device_id': 'shelly-plug-office-01',
    'start': '2024-01-01',
    'end': '2024-01-15'
})
```

### Event Publishing Pattern

```python
# Plugin publishes events
await self.core.publish('device.status', {
    'device_id': 'shelly-plug-office-01',
    'status': 'offline',
    'timestamp': time.now()
})
```

### Streaming Pattern

```python
# Plugin streams metrics
async def stream_metrics(self):
    while True:
        metric = await self.read_sensor()
        yield Metric(
            device_id=self.device_id,
            value=metric.value,
            timestamp=time.now()
        )
        await asyncio.sleep(1)
```

## Integration Examples

### Home Assistant Integration

```yaml
# Home Assistant sensor configuration
sensor:
  - platform: rest
    resource: http://aetherlens.local:8080/api/v1/metrics/current
    name: "Home Power Consumption"
    value_template: "{{ value_json.total_power }}"
    unit_of_measurement: "W"
    
  - platform: rest
    resource: http://aetherlens.local:8080/api/v1/costs/current
    name: "Energy Cost per Hour"
    value_template: "{{ value_json.cost_per_hour }}"
    unit_of_measurement: "$"
```

### Grafana Integration

```json
{
  "name": "AetherLens",
  "type": "prometheus",
  "url": "http://aetherlens.local:8080/metrics",
  "access": "proxy",
  "isDefault": true
}
```

### Node-RED Integration

```javascript
// Node-RED function node
msg.url = "http://aetherlens.local:8080/api/v1/metrics/current";
msg.headers = {
    "Authorization": "Bearer " + env.get("AETHERLENS_TOKEN")
};
return msg;
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-15 | Initial API specification |
| 1.1.0 | TBD | WebSocket subscriptions, GraphQL support |
| 1.2.0 | TBD | Plugin SDK v2, streaming metrics |

---

This specification defines the complete interface for AetherLens Home Edition. All implementations must conform to these interfaces to ensure compatibility and maintainability.