# Testing Guide

## Overview

AetherLens uses **pytest** for all testing. The test suite is comprehensive and includes:

- **Unit Tests** - Fast, isolated logic tests
- **Integration Tests** - Database and component integration
- **API Tests** - REST API endpoint validation
- **Performance Tests** - Response time and throughput benchmarks
- **Security Tests** - Vulnerability and security validation
- **Quality Tests** - Code quality checks

All tests support **Python 3.11 and 3.12** and run automatically in CI/CD pipelines.

______________________________________________________________________

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11 or 3.12
- Development dependencies: `pip install -r requirements-dev.txt`

### Run All Tests Locally

The easiest way to run the full test suite:

```bash
# Linux/macOS
./scripts/test-local.sh

# Windows
scripts\test-local.bat
```

This script will:

1. Start TimescaleDB (port 5433) and Redis (port 6380) containers
1. Wait for services to be healthy
1. Run database migrations
1. Execute all tests with coverage
1. Generate HTML coverage report
1. Clean up containers and volumes

### Run Tests with Makefile

```bash
# Run all tests
make test

# Run specific test categories
make test-unit           # Unit tests only (fast, no services)
make test-integration    # Integration + API tests
make test-api            # API tests only
make test-performance    # Performance benchmarks
make test-security       # Security validation
make test-quality        # Code quality checks

# Run all tests with coverage
make test-all            # Excludes performance tests, generates coverage
make test-coverage       # Full coverage report (HTML + terminal)
```

### Run Tests Directly with pytest

```bash
# All tests
pytest tests/ -v

# Specific test directories
pytest tests/unit/ -v
pytest tests/api/ -v
pytest tests/integration/ -v

# By marker
pytest -m integration         # Integration tests only
pytest -m performance         # Performance tests only
pytest -m security            # Security tests only
pytest -m "not performance"   # Everything except performance

# With coverage
pytest tests/ -v --cov=src/aetherlens --cov-report=html --cov-report=term
```

______________________________________________________________________

## Test Structure

```
tests/
├── unit/                      # Fast, isolated tests
│   ├── test_config.py        # Configuration validation
│   └── test_version.py       # Version checks
│
├── integration/               # Database and system integration
│   ├── test_database.py      # TimescaleDB operations, hypertables
│   └── test_migrations.py    # Schema validation, constraints
│
├── api/                       # REST API endpoint tests
│   ├── test_auth.py          # Authentication endpoints (16 tests)
│   ├── test_health.py        # Health checks (12 tests)
│   └── test_devices.py       # Device CRUD (28 tests)
│
├── performance/               # Performance benchmarks
│   ├── test_api_performance.py       # API response times
│   └── test_database_performance.py  # Query performance
│
├── security/                  # Security validation
│   └── test_security_scans.py # Password hashing, JWT, secrets
│
├── quality/                   # Code quality checks
│   └── __init__.py           # Placeholder for quality tests
│
└── conftest.py               # Shared fixtures (461 lines)
```

**Total: 103+ tests** across all categories

______________________________________________________________________

## Writing Tests

### Unit Tests

Pure logic tests with no external dependencies:

```python
def test_calculate_cost():
    """Test cost calculation logic."""
    from aetherlens.utils import calculate_cost

    result = calculate_cost(power_watts=1000, hours=1, rate=0.24)
    assert result == 0.24

    # Edge case: zero power
    result = calculate_cost(power_watts=0, hours=10, rate=0.24)
    assert result == 0.0
```

**Best Practices:**

- No I/O operations (no database, network, file system)
- Fast execution (\<10ms per test)
- Test one thing per test function
- Use descriptive test names
- Include docstrings explaining what is tested

### API Tests

Use async client fixtures for API endpoint testing:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_devices(authenticated_client: AsyncClient):
    """Test listing devices as authenticated user."""
    response = await authenticated_client.get("/api/v1/devices")

    assert response.status_code == 200
    data = response.json()

    # Verify pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert isinstance(data["items"], list)

@pytest.mark.asyncio
async def test_create_device_forbidden(authenticated_client: AsyncClient):
    """Test that regular users cannot create devices."""
    response = await authenticated_client.post(
        "/api/v1/devices",
        json={
            "name": "Test Device",
            "type": "smart_plug",
            "ip_address": "192.168.1.100",
        },
    )

    # Regular users should get 403 Forbidden
    assert response.status_code == 403
```

**Available Client Fixtures:**

- `api_client` - Unauthenticated client
- `authenticated_client` - Client with user token (regular permissions)
- `admin_client` - Client with admin token (full permissions)

### Integration Tests

Mark with `@pytest.mark.integration` and use database fixtures:

```python
import pytest
import asyncpg

@pytest.mark.integration
@pytest.mark.asyncio
async def test_timescaledb_hypertable(db_pool: asyncpg.Pool):
    """Test that metrics table is a TimescaleDB hypertable."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT hypertable_name
            FROM timescaledb_information.hypertables
            WHERE hypertable_name = 'metrics'
            """
        )

        assert result is not None
        assert result["hypertable_name"] == "metrics"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_rollback(db_pool, sample_device):
    """Test that database transactions rollback properly."""
    device_id = sample_device["device_id"]
    original_name = sample_device["name"]

    async with db_pool.acquire() as conn:
        # Modify data in a transaction
        transaction = conn.transaction()
        await transaction.start()

        await conn.execute(
            "UPDATE devices SET name = $1 WHERE device_id = $2",
            "Modified Name",
            device_id,
        )

        # Rollback
        await transaction.rollback()

        # Verify rollback worked
        current_name = await conn.fetchval(
            "SELECT name FROM devices WHERE device_id = $1",
            device_id,
        )

        assert current_name == original_name
```

**Integration Test Guidelines:**

- Use `db_pool` fixture for database connections
- Mark with `@pytest.mark.integration`
- Test cross-component interactions
- Verify database constraints, triggers, policies
- Each test runs in isolated transaction (auto-rollback)

### Performance Tests

Use `@pytest.mark.performance` for benchmark tests:

```python
import pytest
import time

@pytest.mark.performance
@pytest.mark.asyncio
async def test_health_check_performance(api_client):
    """Test health check response time."""
    times = []

    # Run 10 iterations
    for _ in range(10):
        start = time.time()
        response = await api_client.get("/api/v1/health")
        duration = time.time() - start

        assert response.status_code == 200
        times.append(duration)

    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]

    # Performance assertions
    assert avg_time < 0.1, f"Average time {avg_time:.3f}s > 100ms"
    assert p95_time < 0.2, f"P95 time {p95_time:.3f}s > 200ms"

@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_requests(authenticated_client):
    """Test handling concurrent API requests."""
    import asyncio

    async def make_request():
        response = await authenticated_client.get("/api/v1/devices")
        assert response.status_code == 200

    # 50 concurrent requests
    start = time.time()
    await asyncio.gather(*[make_request() for _ in range(50)])
    duration = time.time() - start

    assert duration < 5.0, f"50 concurrent requests took {duration:.2f}s > 5s"
```

**Performance Test Best Practices:**

- Run multiple iterations (10-100) for statistical significance
- Calculate averages and percentiles (p50, p95, p99)
- Set realistic thresholds based on requirements
- Only run on PRs in CI (not every push)

### Security Tests

Use `@pytest.mark.security` for security validation:

```python
import pytest

@pytest.mark.security
def test_secure_password_hashing():
    """Verify password hashing uses secure algorithms."""
    from aetherlens.security.passwords import hash_password, verify_password
    import time

    # Measure hashing time
    start = time.time()
    hashed = hash_password("test_password_123")
    duration = time.time() - start

    # bcrypt should take at least 50ms (proper cost factor)
    assert duration > 0.05, "Password hashing too fast"

    # Verify bcrypt format
    assert hashed.startswith("$2"), "Password hash not bcrypt format"

    # Verify verification works
    assert verify_password("test_password_123", hashed)
    assert not verify_password("wrong_password", hashed)

@pytest.mark.security
def test_jwt_secret_key_strength():
    """Verify JWT secret key meets minimum security requirements."""
    from aetherlens.config import settings

    secret_key = settings.secret_key

    # Minimum length (32 characters)
    assert len(secret_key) >= 32, "JWT secret key too short"

    # Should not contain weak patterns
    weak_keys = ["secret", "changeme", "password"]
    assert not any(weak in secret_key.lower() for weak in weak_keys), \
        "JWT secret key appears to be weak/default"
```

______________________________________________________________________

## Test Fixtures

Common fixtures available in `tests/conftest.py` (461 lines):

### Configuration Fixtures

```python
test_settings: Settings
```

Test configuration with database/Redis URLs, secret key, debug mode.

### Database Fixtures

```python
db_pool: asyncpg.Pool  # Session-scoped connection pool
db_transaction: asyncpg.Connection  # Function-scoped transaction (auto-rollback)
```

**Important:** All tests automatically use `db_transaction` fixture which wraps each test in a transaction and rolls
back after, ensuring clean state.

### Authentication Fixtures

```python
test_user: Dict  # Regular user account
admin_user: Dict  # Admin user account
user_token: str  # JWT token for test_user
admin_token: str  # JWT token for admin_user
```

### API Client Fixtures

```python
api_client: AsyncClient  # Unauthenticated HTTP client
authenticated_client: AsyncClient  # Client with user token
admin_client: AsyncClient  # Client with admin token
```

### Test Data Fixtures

```python
sample_device: Dict  # Test device with realistic data
sample_metrics: List[Dict]  # 24 hours of time-series metrics (288 data points)
```

**sample_metrics** generates realistic power consumption data:

- 5-minute intervals over 24 hours
- 200W baseline with ±50W variation
- Useful for testing time-series queries, aggregates, and visualizations

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_my_endpoint(authenticated_client, sample_device):
    """Test uses authenticated client and sample device."""
    device_id = sample_device["device_id"]

    response = await authenticated_client.get(f"/api/v1/devices/{device_id}")
    assert response.status_code == 200
```

______________________________________________________________________

## Coverage Requirements

AetherLens enforces code coverage thresholds:

- **Overall Target:** 70% minimum (enforced in CI)
- **Unit Tests:** Should achieve >70% coverage of core logic
- **Integration Tests:** Cover all major workflows and data flows
- **API Tests:** 100% endpoint coverage (all 13 endpoints tested)

### Checking Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src/aetherlens --cov-report=html --cov-report=term

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\index.html  # Windows
```

### Coverage Configuration

- `.codecov.yml` - Codecov settings with 70% target
- `pyproject.toml` - pytest-cov configuration
- GitHub Actions enforces threshold on unit tests

**Note:** Coverage reports are uploaded to Codecov with separate flags for unit and integration tests.

______________________________________________________________________

## CI/CD Testing

GitHub Actions runs tests automatically on every push and pull request:

### Test Jobs

1. **lint** - Code quality checks

   - ruff (linter)
   - black (formatter check)
   - isort (import ordering)
   - mypy (type checking)

1. **test-unit** - Fast unit tests

   - Python 3.11 and 3.12 (matrix)
   - No external services needed
   - Coverage threshold enforcement (>70%)
   - Runs in parallel

1. **test-integration** - Integration and API tests

   - Python 3.11 and 3.12 (matrix)
   - TimescaleDB and Redis services
   - Runs in parallel with unit tests

1. **test-performance** - Performance benchmarks

   - **Only runs on pull requests** (not every push)
   - Python 3.12 only
   - TimescaleDB and Redis services

1. **test-security** - Security validation

   - Python 3.11 and 3.12 (matrix)
   - Validates password hashing, JWT security, no hardcoded secrets

1. **test-quality** - Code quality tests

   - Python 3.11 and 3.12 (matrix)
   - Placeholder for additional quality checks

1. **security** - Security scanning

   - safety (dependency vulnerabilities)
   - bandit (code security issues)

1. **build-docker** - Docker image build

   - Only runs if all tests pass
   - Builds and validates Docker image

1. **test-summary** - Test results summary

   - Aggregates all test results
   - Creates markdown summary table
   - Fails if any tests failed

### Viewing CI Results

- Navigate to GitHub Actions tab
- Click on a workflow run
- View separate jobs for each test category
- Download artifacts for detailed reports
- Check test-summary for overall status

### Local CI Replication

Run the same checks locally before pushing:

```bash
# Lint (matches CI exactly)
make lint

# All tests (matches CI)
./scripts/test-local.sh

# Specific test categories
make test-unit
make test-integration
make test-security
```

______________________________________________________________________

## Troubleshooting

### Tests Failing Locally But Passing in CI

**Possible causes:**

1. **Python version mismatch**

   ```bash
   python --version  # Should be 3.11 or 3.12
   ```

1. **Services not running**

   ```bash
   docker-compose -f docker/docker-compose.test.yml ps
   # Both db-test and redis-test should be "Up (healthy)"
   ```

1. **Port conflicts**

   ```bash
   # Check if ports 5433 or 6380 are in use
   netstat -an | grep 5433
   netstat -an | grep 6380
   ```

1. **Stale database state**

   ```bash
   # Clean up and restart
   docker-compose -f docker/docker-compose.test.yml down -v
   ./scripts/test-local.sh
   ```

### Tests Passing Locally But Failing in CI

**Possible causes:**

1. **Uncommitted files**

   ```bash
   git status  # Check for uncommitted changes
   ```

1. **Missing dependencies**

   ```bash
   # Ensure requirements-dev.txt is up to date
   pip freeze > requirements-dev.txt
   ```

1. **Hardcoded paths or values**

   - Check for absolute paths in test code
   - Verify environment variables are used correctly

### Slow Test Execution

**Optimization strategies:**

1. **Run unit tests only** (no services needed)

   ```bash
   pytest tests/unit/ -v
   ```

1. **Skip performance tests**

   ```bash
   pytest -m "not performance"
   ```

1. **Parallel execution** with pytest-xdist

   ```bash
   pip install pytest-xdist
   pytest tests/ -n auto  # Uses all CPU cores
   ```

1. **Run specific test file**

   ```bash
   pytest tests/api/test_auth.py -v
   ```

### Database State Pollution

Tests should automatically rollback transactions, but if you see state pollution:

**Solution 1: Verify fixtures**

```python
# Ensure your test uses the transaction fixture
async def test_my_database_operation(db_transaction):
    # db_transaction provides connection with auto-rollback
    pass
```

**Solution 2: Manual cleanup**

```bash
# Nuclear option: destroy and recreate database
docker-compose -f docker/docker-compose.test.yml down -v
docker-compose -f docker/docker-compose.test.yml up -d
```

**Solution 3: Check autouse**

```python
# In conftest.py, verify db_transaction has autouse=True
@pytest.fixture(autouse=True)
async def db_transaction(db_pool):
    ...
```

### Import Errors

```bash
# ModuleNotFoundError: No module named 'aetherlens'

# Solution: Install in editable mode
pip install -e .

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Async Test Errors

```python
# RuntimeError: This event loop is already running

# Solution: Use pytest-asyncio properly
import pytest

@pytest.mark.asyncio  # Required for async tests
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Coverage Not Detected

```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Run with coverage explicitly
pytest tests/ --cov=src/aetherlens --cov-report=term
```

______________________________________________________________________

## Best Practices

### General Guidelines

1. **Test Naming**

   - Use descriptive names: `test_user_cannot_delete_other_users_device`
   - Prefix with `test_` for pytest discovery
   - Include docstrings explaining what is tested

1. **Test Organization**

   - One test file per module/endpoint
   - Group related tests in classes (optional)
   - Keep tests close to code they test conceptually

1. **Assertions**

   - Use specific assertions: `assert result == expected`
   - Include failure messages: `assert x > 0, f"Value {x} should be positive"`
   - Test both success and failure cases

1. **Test Data**

   - Use fixtures for reusable test data
   - Avoid hardcoded magic numbers
   - Generate realistic data when possible

1. **Async Testing**

   - Always use `@pytest.mark.asyncio` for async tests
   - Use `await` for all async calls
   - Use `AsyncClient` for API tests

### Anti-Patterns to Avoid

❌ **Don't:**

- Write tests that depend on other tests
- Use `time.sleep()` for synchronization (use proper waits)
- Test implementation details (test behavior)
- Share mutable state between tests
- Ignore test failures ("it works on my machine")

✅ **Do:**

- Make tests independent and isolated
- Use `await asyncio.sleep()` sparingly with timeouts
- Test public APIs and contracts
- Use fixtures to provide clean state
- Fix failing tests immediately

______________________________________________________________________

## Additional Resources

- **pytest Documentation:** https://docs.pytest.org/

- **pytest-asyncio:** https://pytest-asyncio.readthedocs.io/

- **pytest-cov:** https://pytest-cov.readthedocs.io/

- **httpx (AsyncClient):** https://www.python-httpx.org/

- **TimescaleDB Testing:** https://docs.timescale.com/

- **Project Documentation:**

  - [Development Guide](DEVELOPMENT.md)
  - [API Documentation](API.md)
  - [Quick Start Guide](../QUICKSTART.md)
  - [Contributing Guidelines](../CONTRIBUTING.md) (when available)

______________________________________________________________________

**Questions or Issues?**

- Check [GitHub Discussions](https://github.com/aetherlens/home/discussions)
- Report bugs on [GitHub Issues](https://github.com/aetherlens/home/issues)
- Review [CLAUDE.md](../CLAUDE.md) for AI assistant guidelines
