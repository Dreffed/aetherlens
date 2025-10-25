# AetherLens API Documentation

## Overview

AetherLens provides a RESTful API for managing devices, metrics, and cost calculations. The API is built with FastAPI
and includes comprehensive documentation via Swagger UI.

## Base URL

```
http://localhost:8080
```

## Authentication

All API endpoints (except `/health` and `/metrics`) require authentication using JWT Bearer tokens.

### Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

**Response:**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using Tokens

Include the access token in the Authorization header:

```bash
curl http://localhost:8080/api/v1/devices \
  -H "Authorization: Bearer <access_token>"
```

## Rate Limiting

API requests are rate limited to:

- **60 requests per minute** per IP address
- **1000 requests per hour** per IP address

Rate limit headers are included in all responses:

- `X-RateLimit-Limit-Minute`: Maximum requests per minute
- `X-RateLimit-Remaining-Minute`: Remaining requests in current minute
- `X-RateLimit-Limit-Hour`: Maximum requests per hour
- `X-RateLimit-Remaining-Hour`: Remaining requests in current hour

## Health Checks

### Comprehensive Health Check

```bash
GET /health
```

Returns status of all dependencies (database, TimescaleDB).

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-10-24T20:00:00.000Z",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 2.5,
      "message": "Database responding"
    },
    "timescaledb": {
      "status": "healthy",
      "version": "2.22.1",
      "message": "TimescaleDB active"
    }
  }
}
```

### Kubernetes Probes

- **Readiness**: `GET /health/ready` - Returns 200 when ready to accept traffic
- **Liveness**: `GET /health/live` - Returns 200 if process is alive

## Devices

### List Devices

```bash
GET /api/v1/devices?page=1&page_size=50&type=smart_plug
Authorization: Bearer <token>
```

**Query Parameters:**

- `page` (int, default: 1): Page number
- `page_size` (int, default: 50, max: 100): Items per page
- `type` (string, optional): Filter by device type

**Response:**

```json
{
  "devices": [
    {
      "device_id": "shelly-office-01",
      "name": "Office Desk Plug",
      "type": "smart_plug",
      "manufacturer": "Shelly",
      "model": "Plug S",
      "location": {"room": "office", "floor": 2},
      "capabilities": ["power_monitoring", "on_off_control"],
      "configuration": {"ip_address": "192.168.1.100"},
      "status": {"online": true},
      "created_at": "2025-10-24T10:00:00Z",
      "updated_at": "2025-10-24T15:30:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 50,
  "pages": 1
}
```

### Get Device

```bash
GET /api/v1/devices/{device_id}
Authorization: Bearer <token>
```

### Create Device (Admin Only)

```bash
POST /api/v1/devices
Authorization: Bearer <token>
Content-Type: application/json

{
  "device_id": "new-device-01",
  "name": "New Smart Plug",
  "type": "smart_plug",
  "manufacturer": "Shelly",
  "model": "Plug S",
  "location": {"room": "bedroom", "floor": 2},
  "capabilities": ["power_monitoring"],
  "configuration": {"ip_address": "192.168.1.105"}
}
```

### Update Device (Admin Only)

```bash
PUT /api/v1/devices/{device_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Device Name",
  "location": {"room": "living_room", "floor": 1}
}
```

### Delete Device (Admin Only)

```bash
DELETE /api/v1/devices/{device_id}
Authorization: Bearer <token>
```

**Note:** Deleting a device will also delete all associated metrics.

## Metrics (Prometheus)

```bash
GET /metrics
```

Exposes Prometheus-formatted metrics:

- `aetherlens_api_requests_total` - Total API requests by method, endpoint, status
- `aetherlens_api_request_duration_seconds` - Request duration histogram
- `aetherlens_api_requests_in_progress` - Current in-progress requests
- `aetherlens_database_pool_size` - Database connection pool size
- `aetherlens_database_pool_available` - Available database connections

## Interactive Documentation

Visit these URLs for interactive API documentation:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `204 No Content` - Success with no response body
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service unhealthy

## Example: Complete Workflow

### 1. Login

```bash
TOKEN=$(curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')
```

### 2. Check Health

```bash
curl http://localhost:8080/health | jq
```

### 3. List Devices

```bash
curl http://localhost:8080/api/v1/devices \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 4. Create Device

```bash
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-plug-01",
    "name": "Test Smart Plug",
    "type": "smart_plug",
    "manufacturer": "Test",
    "capabilities": ["power_monitoring"]
  }' | jq
```

### 5. Get Device

```bash
curl http://localhost:8080/api/v1/devices/test-plug-01 \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 6. View Metrics

```bash
curl http://localhost:8080/metrics | grep aetherlens
```

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn aetherlens.api.main:app --reload --host 0.0.0.0 --port 8080
```

### Running with Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f aetherlens-api

# Stop services
docker-compose down
```

## Performance Targets

| Metric                  | Target  |
| ----------------------- | ------- |
| API response time (p50) | \<50ms  |
| API response time (p95) | \<200ms |
| API response time (p99) | \<500ms |
| Requests per second     | >1000   |
| Concurrent connections  | >100    |
| Memory usage (idle)     | \<256MB |
| Startup time            | \<5s    |

## Security

- All passwords are hashed using bcrypt
- JWT tokens expire after 1 hour (access) or 7 days (refresh)
- Rate limiting prevents abuse
- CORS is configured (update for production)
- All database queries use parameterized statements
- Request IDs enable request tracing

## Support

For issues or questions:

- GitHub Issues: https://github.com/aetherlens/home/issues
- Documentation: https://docs.aetherlens.io
- Discord: https://discord.gg/aetherlens
