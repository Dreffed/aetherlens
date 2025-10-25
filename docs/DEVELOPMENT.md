# Development Guide

## Getting Started

### Prerequisites

- Python 3.11 or 3.12
- Docker and Docker Compose (for database and testing)
- Git
- Make (optional, but recommended)

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aetherlens/home.git
   cd aetherlens
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv

   # On Windows
   .\venv\Scripts\activate

   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   make install-dev
   # OR
   pip install -r requirements-dev.txt
   pip install -e .
   ```

4. **Install pre-commit hooks:**
   ```bash
   make pre-commit-install
   # OR
   pip install pre-commit
   pre-commit install
   ```

5. **Verify setup:**
   ```bash
   make lint
   ```

---

## Code Quality & Linting

### Why Linting Matters

Local linting ensures:
- ✅ Your code passes CI checks **before** pushing
- ✅ Consistent code style across the project
- ✅ Type safety with mypy
- ✅ Early detection of common bugs
- ✅ Faster development cycle (no waiting for CI failures)

### Quick Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `make lint` | Run all linters (matches CI exactly) | **Before every commit/push** |
| `make format` | Auto-fix formatting issues | When lint fails on style |
| `./scripts/lint.sh` | Bash script for linting | Alternative to make |
| `scripts\lint.bat` | Windows batch script | Windows cmd.exe users |
| `pre-commit run --all-files` | Run pre-commit hooks manually | Testing pre-commit setup |

### Linting Workflow

#### Method 1: Makefile (Recommended)

```bash
# Run all linters (matches GitHub Actions exactly)
make lint

# If formatting issues, auto-fix them
make format

# Run lint again to verify
make lint
```

#### Method 2: Direct Scripts

**On Linux/Mac/Git Bash:**
```bash
./scripts/lint.sh
```

**On Windows (cmd.exe):**
```cmd
scripts\lint.bat
```

#### Method 3: Manual Commands

Run the exact same commands as GitHub Actions:

```bash
# 1. Ruff linting
ruff check src/ tests/

# 2. Black formatting check
black --check src/ tests/

# 3. isort import ordering
isort --check-only src/ tests/

# 4. mypy type checking
mypy src/
```

### Pre-Commit Hooks

Pre-commit hooks run automatically on `git commit` and prevent commits with linting issues.

**Install hooks:**
```bash
make pre-commit-install
```

**What runs on commit:**
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Ruff linting (with auto-fix)
- Black formatting (auto-fix)
- isort import sorting (auto-fix)
- mypy type checking (src/ only)
- Bandit security checks

**Skip hooks temporarily (not recommended):**
```bash
git commit --no-verify -m "WIP: temp commit"
```

**Update pre-commit hooks:**
```bash
pre-commit autoupdate
```

### Understanding Linting Errors

#### Ruff Errors

```bash
src/aetherlens/api/main.py:45:80: E501 Line too long (88 > 79 characters)
```

**Fix:** Break line into multiple lines or disable for specific line:
```python
# Disable for one line
some_long_function_call()  # noqa: E501

# Better: Break into multiple lines
result = some_long_function_call(
    argument1,
    argument2,
    argument3
)
```

#### Black Errors

```bash
would reformat src/aetherlens/api/main.py
```

**Fix:** Run black to auto-format:
```bash
black src/ tests/
# OR
make format
```

#### isort Errors

```bash
ERROR: src/aetherlens/api/main.py Imports are incorrectly sorted
```

**Fix:** Run isort to auto-sort:
```bash
isort src/ tests/
# OR
make format
```

#### mypy Errors

```bash
src/aetherlens/api/main.py:50: error: Argument 1 to "create_user" has incompatible type "str"; expected "int"
```

**Fix:** Add proper type hints or fix type mismatch:
```python
# Before
def create_user(user_id: int) -> User:
    ...

create_user("123")  # Error!

# After
def create_user(user_id: int) -> User:
    ...

create_user(123)  # OK
```

### Continuous Integration (CI)

Our GitHub Actions workflow runs on every push and PR:

1. **Lint Job** - Runs all linters (same as `make lint`)
2. **Unit Tests** - Python 3.11 & 3.12
3. **Integration Tests** - With TimescaleDB and Redis
4. **Security Scan** - safety and bandit
5. **Docker Build** - Validates Dockerfile

**To ensure CI passes:**
```bash
# Before pushing to GitHub
make lint
make test

# If all pass locally, CI should pass too
git push origin your-branch
```

---

## Testing

See [TESTING.md](./TESTING.md) for comprehensive testing documentation.

### Quick Test Commands

```bash
# Run all tests
make test

# Run specific test categories
make test-unit            # Fast unit tests
make test-integration     # Integration tests (requires Docker)
make test-api             # API endpoint tests
make test-performance     # Performance benchmarks

# Run with coverage
make test-coverage

# Docker-based testing
make docker-test
```

---

## Database Operations

### Running Migrations

```bash
# Start database
docker-compose -f docker/docker-compose.yml up -d db

# Run migrations
make db-migrate

# Backup database
make db-backup
```

### Connect to Database

```bash
# PostgreSQL CLI
docker-compose -f docker/docker-compose.yml exec db psql -U postgres -d aetherlens

# Check TimescaleDB
SELECT * FROM timescaledb_information.hypertables;
```

---

## Development Workflow

### Feature Development

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test frequently:**
   ```bash
   # After making changes
   make lint
   make test-unit
   ```

3. **Commit changes:**
   ```bash
   # Pre-commit hooks run automatically
   git add .
   git commit -m "feat: add new feature"
   ```

4. **Run full test suite:**
   ```bash
   make lint
   make test
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

### Bug Fixes

1. **Write failing test first** (TDD):
   ```bash
   # Create test that reproduces bug
   # Run test to verify it fails
   pytest tests/unit/test_bugfix.py -v
   ```

2. **Fix the bug:**
   ```python
   # Make minimal changes to fix
   ```

3. **Verify fix:**
   ```bash
   # Test should now pass
   pytest tests/unit/test_bugfix.py -v

   # Run full suite
   make test
   ```

4. **Lint and commit:**
   ```bash
   make lint
   git commit -m "fix: resolve issue with X"
   ```

---

## Code Style Guide

### Python Style

We follow PEP 8 with these specifics:

- **Line length:** 88 characters (Black default)
- **Imports:** Sorted with isort (stdlib, third-party, local)
- **Quotes:** Double quotes preferred
- **Type hints:** Required for all public functions
- **Docstrings:** Google style

### Example

```python
"""Module docstring describing purpose."""

from typing import List, Optional
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends

from aetherlens.api.database import db_manager
from aetherlens.models.device import DeviceResponse

logger = structlog.get_logger()
router = APIRouter()


async def get_devices(
    limit: int = 50,
    offset: int = 0,
) -> List[DeviceResponse]:
    """
    Retrieve devices with pagination.

    Args:
        limit: Maximum number of devices to return
        offset: Number of devices to skip

    Returns:
        List of device objects

    Raises:
        DatabaseError: If database query fails

    Example:
        >>> devices = await get_devices(limit=10)
        >>> len(devices)
        10
    """
    pool = db_manager.get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM devices LIMIT $1 OFFSET $2",
            limit,
            offset
        )

    return [DeviceResponse(**dict(row)) for row in rows]
```

### Type Hints

```python
# ✅ Good - Explicit types
async def calculate_cost(
    power_watts: float,
    duration_hours: float,
    rate_per_kwh: float,
) -> float:
    """Calculate energy cost."""
    return (power_watts * duration_hours / 1000) * rate_per_kwh

# ❌ Bad - No type hints
async def calculate_cost(power_watts, duration_hours, rate_per_kwh):
    return (power_watts * duration_hours / 1000) * rate_per_kwh
```

### Async/Await

```python
# ✅ Good - Async for I/O operations
async def fetch_device_data(device_id: str) -> Dict:
    """Fetch device data from database."""
    pool = db_manager.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM devices WHERE device_id = $1",
            device_id
        )

# ❌ Bad - Blocking call in async function
async def fetch_device_data(device_id: str) -> Dict:
    import time
    time.sleep(1)  # Blocks event loop!
    return {}
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

```
ModuleNotFoundError: No module named 'aetherlens'
```

**Solution:**
```bash
pip install -e .
```

#### 2. Pre-commit Hook Failures

```
black....................................................................Failed
```

**Solution:**
```bash
# Auto-fix formatting
make format

# Commit again
git commit -m "your message"
```

#### 3. Docker Database Not Starting

```
Error: Connection refused
```

**Solution:**
```bash
# Check container status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs db

# Restart
docker-compose -f docker/docker-compose.yml restart db
```

#### 4. Mypy Type Errors

```
error: Cannot determine type of 'result'
```

**Solution:**
```python
# Add explicit type annotation
result: Optional[Dict[str, Any]] = await conn.fetchrow(...)
```

---

## Tools & IDE Setup

### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Ruff
- Black Formatter
- isort

**settings.json:**
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.linting.mypyEnabled": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

1. **Settings → Tools → Black:** Enable on save
2. **Settings → Tools → isort:** Enable on save
3. **Settings → Editor → Inspections:** Enable mypy

---

## Additional Resources

- [API Documentation](./API.md)
- [Testing Guide](./TESTING.md)
- [Plugin Development](./PLUGIN_GUIDE.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [Black Code Style](https://black.readthedocs.io/en/stable/the_black_code_style/)

---

## Getting Help

- **GitHub Discussions:** Ask questions and share ideas
- **GitHub Issues:** Report bugs and request features
- **Discord:** Real-time chat with maintainers and community

---

**Happy coding! 🚀**
