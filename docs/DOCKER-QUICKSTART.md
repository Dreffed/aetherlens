# Docker Quick Start Guide

Get AetherLens running with Docker in minutes!

## Prerequisites

- Docker 20.10 or later
- Docker Compose 2.0 or later
- 2GB free RAM
- 10GB free disk space

## Quick Start (3 Steps)

### Step 1: Generate Secret Key

**IMPORTANT:** You MUST generate a secure SECRET_KEY before starting the containers.

**Linux/macOS:**

```bash
# Generate and create .env file automatically
python scripts/generate-secret-key.py --env

# Or manually generate and copy
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Windows (PowerShell):**

```powershell
# Generate and create .env file automatically
python scripts\generate-secret-key.py --env

# Or manually generate
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Windows (Command Prompt):**

```cmd
REM Generate and create .env file automatically
scripts\generate-secret-key.bat --env
```

### Step 2: Start Services

```bash
# Navigate to docker directory
cd docker

# Start all services
docker-compose up -d

# Watch logs (optional)
docker-compose logs -f
```

### Step 3: Verify Installation

```bash
# Check service status
docker-compose ps

# Test API health
curl http://localhost:8080/api/v1/health

# Or open in browser
http://localhost:8080/api/v1/health
```

You should see output like:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-25T14:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "timescaledb": "healthy"
  }
}
```

## What's Running?

After `docker-compose up -d`, you'll have:

| Service                | Port | Description                 |
| ---------------------- | ---- | --------------------------- |
| **AetherLens API**     | 8080 | Main application and web UI |
| **Prometheus Metrics** | 9090 | Metrics endpoint            |
| **TimescaleDB**        | 5432 | Time-series database        |
| **Redis**              | 6379 | Caching and session storage |

## Common Issues

### Issue: Container keeps restarting

**Symptom:**

```bash
$ docker-compose ps
NAME                STATUS
aetherlens          Restarting (1)
```

**Cause:** SECRET_KEY is too short (must be ≥32 characters)

**Solution:**

```bash
# Generate a new secret key
python scripts/generate-secret-key.py --env --force

# Restart containers
docker-compose restart
```

**Check logs:**

```bash
docker logs aetherlens
```

### Issue: Database connection failed

**Symptom:** Logs show "could not connect to database"

**Solution:**

```bash
# Wait for database to be fully ready (can take 30-40 seconds)
docker-compose logs timescaledb

# Look for: "database system is ready to accept connections"

# Restart aetherlens container
docker-compose restart aetherlens
```

### Issue: Port already in use

**Symptom:** "port is already allocated"

**Solution:**

```bash
# Check what's using the port
netstat -ano | grep :8080  # Linux/macOS
netstat -ano | findstr :8080  # Windows

# Either stop the conflicting service or change AetherLens port
# Edit docker/docker-compose.yml and change ports:
    ports:
      - "8081:8080"  # Use port 8081 instead of 8080
```

### Issue: Out of disk space

**Symptom:** Database or logs filling disk

**Solution:**

```bash
# View disk usage
docker system df

# Clean up old data
docker system prune -a

# Configure retention policies (edit .env)
METRICS_RETENTION_DAYS=30  # Default is 90
```

## Managing Services

### Start/Stop

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose stop

# Stop and remove containers (keeps data)
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f aetherlens
docker-compose logs -f timescaledb

# Last 100 lines
docker-compose logs --tail=100 aetherlens
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart aetherlens
```

### Update to Latest Version

```bash
# Pull latest code
git pull origin master

# Rebuild images
docker-compose build --no-cache

# Restart with new images
docker-compose up -d
```

## Environment Configuration

### Using .env File (Recommended)

Create a `.env` file in the project root:

```bash
# Generate .env with secure SECRET_KEY
python scripts/generate-secret-key.py --env
```

Or manually create `.env`:

```bash
# Security
SECRET_KEY=your-very-secure-random-string-at-least-32-characters-long

# Database
DB_PASSWORD=aetherlens_pass

# Application
DEBUG=false
LOG_LEVEL=info
TZ=America/New_York
```

### Using Environment Variables

```bash
# Export before running docker-compose
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export DB_PASSWORD="your_db_password"

docker-compose up -d
```

### Using docker-compose Override

Create `docker/docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  aetherlens:
    environment:
      - SECRET_KEY=your-secure-key-here
      - DEBUG=true
    ports:
      - "8081:8080"  # Use different port
```

## Data Persistence

All data is stored in Docker volumes:

```bash
# List volumes
docker volume ls | grep aetherlens

# Backup database
docker-compose exec timescaledb pg_dump -U postgres aetherlens > backup.sql

# Restore database
docker-compose exec -T timescaledb psql -U postgres aetherlens < backup.sql

# Remove all data (CAREFUL!)
docker-compose down -v
```

## Accessing Services

### API Documentation

- **Health Check:** http://localhost:8080/api/v1/health
- **API Docs (Swagger):** http://localhost:8080/docs
- **API Docs (ReDoc):** http://localhost:8080/redoc

### Database Access

```bash
# Connect via Docker
docker-compose exec timescaledb psql -U postgres -d aetherlens

# Or from host (if psql installed)
psql -h localhost -p 5432 -U postgres -d aetherlens
```

### Redis Access

```bash
# Connect via Docker
docker-compose exec redis redis-cli

# From host (if redis-cli installed)
redis-cli -h localhost -p 6379
```

## Production Deployment

### Security Checklist

- [ ] Generate strong SECRET_KEY (32+ characters)
- [ ] Change DB_PASSWORD from default
- [ ] Set DEBUG=false
- [ ] Configure firewall rules
- [ ] Use HTTPS reverse proxy (nginx, traefik)
- [ ] Set up log rotation
- [ ] Configure backup automation
- [ ] Review retention policies

### Recommended Production Setup

```bash
# Use docker-compose.prod.yml for production
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

### Monitoring

```bash
# View metrics
curl http://localhost:9090/metrics

# Check container health
docker-compose ps
docker stats
```

## Next Steps

1. **Configure Devices** - Add your devices and sensors
1. **Set Up Integrations** - Connect cloud accounts (Azure, AWS, etc.)
1. **Install Plugins** - Add support for Shelly, Tasmota, Home Assistant
1. **Configure Alerts** - Set up cost/usage notifications
1. **Explore API** - Visit http://localhost:8080/docs

## Getting Help

- **Documentation:** See [docs/](../docs/) folder
- **Issues:** https://github.com/aetherlens/home/issues
- **Discussions:** https://github.com/aetherlens/home/discussions
- **Discord:** [Join our community](#)

## Troubleshooting Commands

```bash
# Full diagnostic output
docker-compose ps
docker-compose logs --tail=50
docker stats --no-stream

# Check container health
docker inspect aetherlens | grep Health -A 20

# Restart from scratch (keeps data)
docker-compose down
docker-compose up -d

# Complete reset (deletes all data)
docker-compose down -v
docker volume prune
docker-compose up -d
```

______________________________________________________________________

**Need more help?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or ask in GitHub Discussions!
