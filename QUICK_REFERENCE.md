# AetherLens Quick Reference Card

## 🎯 Project Overview

**Name:** AetherLens Home Edition\
**Purpose:** Open-source cost and usage monitoring for home labs, smart homes, and personal cloud\
**License:** MIT\
**Language:** Python 3.11+ (core), TypeScript (UI)\
**Target:** Home lab enthusiasts, self-hosters, smart home users

______________________________________________________________________

## 📁 File Guide

| File                | Purpose         | Read When...                  |
| ------------------- | --------------- | ----------------------------- |
| **README.md**       | Project intro   | First time visitor            |
| **ARCHITECTURE.md** | System design   | Building/understanding system |
| **SCHEMA.md**       | Database design | Working with data/storage     |
| **INTERFACES.md**   | APIs & plugins  | Building integrations         |
| **CLAUDE.md**       | Dev guidelines  | Writing code                  |

______________________________________________________________________

## 🏗️ Architecture Quick Facts

### Core Stack

- **Language:** Python 3.11+ (FastAPI)
- **Database:** TimescaleDB (PostgreSQL + time-series)
- **Cache:** Redis (optional)
- **Frontend:** React 18 + TypeScript + Tailwind
- **Deployment:** Docker Compose

### Key Components

```
Devices → Plugins → Collector → Processor → Storage → API → UI
            ↓         ↓           ↓          ↓
         Isolated  Buffered   Enriched   Persisted
```

### Resource Targets

- **Memory:** \<1 GB total (core + plugins + DB)
- **CPU:** \<10% idle, \<35% active
- **Storage:** ~50 MB/day for 100 devices
- **Network:** Minimal (local LAN only)

______________________________________________________________________

## 🔌 Plugin Quick Start

### Minimal Plugin

```python
from aetherlens_sdk import BasePlugin, Metric

class MyPlugin(BasePlugin):
    async def collect_metrics(self) -> List[Metric]:
        return [
            Metric(
                device_id="my-device",
                timestamp=time.time(),
                metric_type="power",
                value=100.0,
                unit="watts"
            )
        ]
```

### Plugin Manifest (plugin.yaml)

```yaml
id: my-plugin
name: My Custom Plugin
version: 1.0.0
author: Your Name
runtime:
  type: python
  version: "3.11"
  entrypoint: my_plugin.py
capabilities:
  - metrics.collect
```

______________________________________________________________________

## 🗄️ Database Quick Reference

### Create Hypertable

```sql
CREATE TABLE metrics (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    tags JSONB DEFAULT '{}'
);

SELECT create_hypertable('metrics', 'time');
```

### Common Queries

```sql
-- Get last 24h power consumption
SELECT device_id, AVG(value) as avg_watts
FROM metrics
WHERE time > NOW() - INTERVAL '24 hours'
  AND metric_type = 'power'
GROUP BY device_id;

-- Get hourly aggregates
SELECT 
    time_bucket('1 hour', time) AS hour,
    device_id,
    AVG(value) as avg_value,
    MAX(value) as max_value
FROM metrics
WHERE time > NOW() - INTERVAL '7 days'
GROUP BY hour, device_id
ORDER BY hour DESC;
```

______________________________________________________________________

## 🔐 Security Checklist

### Must Do

- ✅ Store credentials in platform keyring
- ✅ Use HTTPS/TLS for external access
- ✅ JWT tokens for API authentication
- ✅ Input validation with Pydantic
- ✅ SQL parameterization (no string concat)
- ✅ Rate limiting on API endpoints

### Never Do

- ❌ Hardcode credentials
- ❌ Store passwords in plaintext
- ❌ Use SQL string concatenation
- ❌ Expose API without authentication
- ❌ Allow unlimited requests
- ❌ Run plugins as root

______________________________________________________________________

## 🌐 API Quick Reference

### Authentication

```bash
# Get token
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token
curl http://localhost:8080/api/v1/metrics/current \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Key Endpoints

| Endpoint                  | Method         | Purpose            |
| ------------------------- | -------------- | ------------------ |
| `/api/v1/metrics/current` | GET            | Current metrics    |
| `/api/v1/metrics/history` | GET            | Historical data    |
| `/api/v1/devices`         | GET/POST       | Device management  |
| `/api/v1/devices/{id}`    | GET/PUT/DELETE | Device operations  |
| `/api/v1/costs/current`   | GET            | Current costs      |
| `/api/v1/costs/summary`   | GET            | Cost summary       |
| `/metrics`                | GET            | Prometheus metrics |

______________________________________________________________________

## 🚀 Quick Start Commands

### Docker Compose

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f aetherlens

# Stop
docker-compose down

# Reset (delete all data)
docker-compose down -v
```

### Development

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Run tests
pytest tests/
npm test

# Start development server
python -m aetherlens.server --dev
npm run dev

# Run linters
ruff check .
eslint src/
```

______________________________________________________________________

## 📊 Common Patterns

### Async Collection

```python
async def collect_from_devices(devices):
    tasks = [collect_single(d) for d in devices]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

### Retry with Backoff

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### Circuit Breaker

```python
breaker = CircuitBreaker(failure_threshold=5, timeout=60)
result = await breaker.call(unreliable_function, arg1, arg2)
```

______________________________________________________________________

## 🧪 Testing Quick Guide

### Unit Test

```python
def test_cost_calculation():
    calculator = CostCalculator(rate=0.24)
    cost = calculator.calculate(power_watts=1000, hours=1)
    assert cost == pytest.approx(0.24)
```

### Integration Test

```python
@pytest.mark.asyncio
async def test_end_to_end():
    plugin = await manager.load_plugin("test_plugin")
    metrics = await plugin.collect_metrics()
    await collector.collect_batch(metrics)
    assert await db.count("metrics") > 0
```

### Performance Test

```python
@pytest.mark.benchmark
async def test_bulk_insert_speed():
    metrics = generate_test_metrics(count=10000)
    start = time.time()
    await batch_insert_metrics(metrics)
    assert time.time() - start < 5.0  # Under 5 seconds
```

______________________________________________________________________

## 🐛 Troubleshooting

### High Memory Usage

```bash
# Check memory by process
docker stats aetherlens

# Enable memory profiling
import tracemalloc
tracemalloc.start()
# ... your code ...
snapshot = tracemalloc.take_snapshot()
```

### Plugin Not Loading

```bash
# Check plugin logs
tail -f /opt/aetherlens/logs/plugins/my-plugin.log

# Validate plugin manifest
python -m aetherlens.tools validate-plugin plugins/my-plugin/

# Test plugin in isolation
python -m aetherlens.tools test-plugin my-plugin
```

### Slow Queries

```sql
-- Check query performance
EXPLAIN ANALYZE
SELECT * FROM metrics WHERE device_id = 'device-01' AND time > NOW() - INTERVAL '24 hours';

-- Check missing indexes
SELECT * FROM timescaledb_information.hypertables;
SELECT * FROM pg_indexes WHERE tablename = 'metrics';
```

______________________________________________________________________

## 📚 Important Links

### Documentation

- [README.md](./README.md) - Project overview
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
- [SCHEMA.md](./SCHEMA.md) - Database schema
- [INTERFACES.md](./INTERFACES.md) - API specifications
- [CLAUDE.md](./CLAUDE.md) - Development guidelines

### External Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [TimescaleDB Docs](https://docs.timescale.com/)
- [React Docs](https://react.dev/)
- [Python AsyncIO](https://docs.python.org/3/library/asyncio.html)

### Community

- Discord: discord.gg/aetherlens (to be created)
- GitHub: github.com/aetherlens/home
- Forum: community.aetherlens.io (to be created)

______________________________________________________________________

## 🎓 Learning Path

### Week 1: Foundation

1. Read README.md (project overview)
1. Study ARCHITECTURE.md (system design)
1. Review SCHEMA.md (database design)
1. Set up development environment

### Week 2-3: Core Development

1. Follow CLAUDE.md coding standards
1. Implement first plugin using INTERFACES.md
1. Write tests for plugin
1. Set up TimescaleDB and test queries

### Week 4: Integration

1. Connect plugin to core system
1. Build simple UI to display metrics
1. Add cost calculation
1. Deploy using Docker Compose

______________________________________________________________________

## ⚠️ Common Pitfalls

1. **Forgetting async/await** → Blocks event loop
1. **No error handling** → Silent failures
1. **Hardcoded credentials** → Security risk
1. **Loading all data in memory** → OOM crashes
1. **No connection pooling** → Performance issues
1. **Missing indexes** → Slow queries
1. **No rate limiting** → API abuse
1. **Ignoring time zones** → Wrong cost calculations

______________________________________________________________________

## 📝 Quick Commands Reference

```bash
# Docker
docker-compose up -d                    # Start services
docker-compose logs -f aetherlens       # View logs
docker-compose down                     # Stop services
docker-compose down -v                  # Stop and delete data

# Database
psql -U postgres -d aetherlens          # Connect to DB
\dt                                     # List tables
\d metrics                              # Describe table
SELECT count(*) FROM metrics;           # Count records

# Python
pip install -r requirements.txt         # Install deps
pytest tests/ -v                        # Run tests
pytest tests/ --cov                     # Run with coverage
python -m aetherlens.server             # Start server
python -m aetherlens.server --dev       # Dev mode

# Git
git add .                               # Stage all
git commit -m "feat: description"       # Commit
git push origin feature-branch          # Push branch

# Tools
curl http://localhost:8080/health       # Health check
curl http://localhost:8080/metrics      # Prometheus metrics
```

______________________________________________________________________

## 🎯 Development Priorities

### Phase 1 (MVP - 3 months)

1. Core collector and storage
1. First 3 plugins (Shelly, Home Assistant, AWS)
1. Basic cost calculation
1. Simple web UI
1. Docker deployment

### Phase 2 (Growth - 3 months)

6. 10 more plugins
1. Advanced cost features (TOU rates)
1. Mobile app
1. Anomaly detection
1. Plugin marketplace

### Phase 3 (Maturity - 6 months)

11. Advanced analytics
01. ML predictions
01. Automation features
01. Multi-home support
01. Enterprise features

______________________________________________________________________

## 💡 Pro Tips

1. **Read the docs first** - Save time, avoid mistakes
1. **Start with examples** - Adapt working code
1. **Test early and often** - Catch bugs early
1. **Profile before optimizing** - Focus on real bottlenecks
1. **Log with context** - Makes debugging easier
1. **Document decisions** - Future you will thank you
1. **Ask for help** - Community is friendly
1. **Contribute back** - Help others learn

______________________________________________________________________

**Last Updated:** October 21, 2025\
**Version:** 1.0.0\
**Status:** Ready for Development

*This quick reference provides fast access to common information. For detailed documentation, refer to the individual
markdown files.*
