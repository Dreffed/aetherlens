# Contributing to AetherLens

Thank you for your interest in contributing to **AetherLens Home Edition**! This document provides guidelines and requirements for contributing to the project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing Requirements](#testing-requirements)
- [Code Quality Standards](#code-quality-standards)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)

---

## Code of Conduct

This project adheres to a code of conduct adapted from the Contributor Covenant. By participating, you are expected to:

- Be respectful and inclusive
- Welcome newcomers and beginners
- Focus on what is best for the community
- Show empathy towards other community members

**Unacceptable behavior includes:**
- Harassment, discrimination, or hostile language
- Publishing others' private information
- Trolling or insulting comments
- Any conduct that could be considered unprofessional

---

## Getting Started

### Prerequisites

- **Python 3.11 or 3.12** (required)
- **Git** for version control
- **Docker and Docker Compose** for local testing
- **Code editor** with Python support (VS Code, PyCharm, etc.)

### First-Time Setup

1. **Fork the repository** on GitHub

2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/aetherlens.git
   cd aetherlens
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/aetherlens/home.git
   ```

4. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

5. **Install pre-commit hooks:**
   ```bash
   make pre-commit-install
   ```

6. **Verify setup:**
   ```bash
   make lint
   ./scripts/test-local.sh
   ```

---

## Development Setup

### Development Environment

We recommend using a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
pip install -e .
```

### Pre-commit Hooks

Pre-commit hooks automatically check code quality before commits:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**Hooks include:**
- ruff (linting)
- black (formatting)
- isort (import sorting)
- mypy (type checking)

These match **exactly** what runs in CI, preventing surprises.

### IDE Setup

**Visual Studio Code:**
- Install Python extension
- Use `.vscode/settings.json` for project settings
- Enable formatOnSave for black
- Configure pytest as test runner

**PyCharm:**
- Mark `src/` as Sources Root
- Configure pytest as default test runner
- Enable black and ruff in settings
- Set up run configurations for tests

---

## Making Changes

### Branching Strategy

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Keep branch up to date:**
   ```bash
   git fetch upstream
   git rebase upstream/master
   ```

### Commit Messages

Write clear, descriptive commit messages:

**Format:**
```
<type>: <short summary> (<50 chars)

<detailed description if needed>

<optional footer with issue references>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

**Examples:**
```
feat: Add device auto-discovery for Shelly plugs

Implement mDNS discovery for Shelly smart plugs on local network.
Devices are automatically added to device list with default settings.

Closes #123
```

```
fix: Resolve race condition in metrics collection

Use database-level locking to prevent concurrent writes to the same
device metrics. Adds unique constraint on (device_id, timestamp).

Fixes #456
```

### Code Style

Follow the project's code style (enforced by pre-commit hooks):

**Python:**
- **PEP 8** compliant (via ruff and black)
- **Type hints** on all function signatures
- **Docstrings** for all public APIs (Google style)
- **Async/await** for all I/O operations
- **Descriptive names** over comments

**Example:**
```python
async def collect_device_metrics(
    device_id: str,
    start_time: datetime,
    end_time: datetime
) -> List[Metric]:
    """
    Collect metrics for a device within a time range.

    Args:
        device_id: Unique identifier for the device
        start_time: Start of time range (inclusive)
        end_time: End of time range (inclusive)

    Returns:
        List of metric data points

    Raises:
        DeviceOfflineError: If device is not reachable
        ValueError: If time range is invalid
    """
    if start_time >= end_time:
        raise ValueError("start_time must be before end_time")

    # Implementation...
```

---

## Testing Requirements

**All contributions must include tests.** This is non-negotiable for maintaining code quality.

### Test Coverage

- **New features:** Must include unit + integration tests
- **Bug fixes:** Must include regression test
- **Minimum coverage:** 70% overall (enforced in CI)
- **API changes:** Must have 100% endpoint coverage

### Writing Tests

Create tests in the appropriate directory:

```
tests/
├── unit/              # Fast, isolated logic tests
├── integration/       # Database and system integration
├── api/               # REST API endpoint tests
├── performance/       # Performance benchmarks
└── security/          # Security validation
```

**Unit Test Example:**
```python
def test_power_consumption_calculation():
    """Test power consumption calculation."""
    from aetherlens.calculations import calculate_power_cost

    # 1000W for 2 hours at $0.24/kWh
    cost = calculate_power_cost(
        power_watts=1000,
        duration_hours=2,
        rate_per_kwh=0.24
    )

    assert cost == 0.48
```

**API Test Example:**
```python
import pytest

@pytest.mark.asyncio
async def test_create_device_requires_admin(authenticated_client):
    """Test that only admins can create devices."""
    response = await authenticated_client.post(
        "/api/v1/devices",
        json={"name": "Test", "type": "smart_plug"}
    )

    # Regular user should get 403 Forbidden
    assert response.status_code == 403
```

**Integration Test Example:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_stored_in_hypertable(db_pool, sample_device):
    """Test that metrics are correctly stored in TimescaleDB hypertable."""
    async with db_pool.acquire() as conn:
        # Insert metric
        await conn.execute(
            """
            INSERT INTO metrics (time, device_id, metric_type, value, unit)
            VALUES (NOW(), $1, 'power', 125.5, 'watts')
            """,
            sample_device["device_id"]
        )

        # Verify stored
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM metrics WHERE device_id = $1",
            sample_device["device_id"]
        )

        assert count == 1
```

### Running Tests

**Before submitting:**

```bash
# Run all tests locally
./scripts/test-local.sh

# Or use Makefile
make test-all

# Verify linting
make lint
```

**Quick checks:**

```bash
# Run only your new tests
pytest tests/api/test_my_feature.py -v

# Check coverage
pytest tests/ --cov=src/aetherlens --cov-report=term
```

### Test Guidelines

✅ **Do:**
- Write independent, isolated tests
- Use descriptive test names
- Test both success and error cases
- Use fixtures from `conftest.py`
- Add docstrings to tests
- Mock external services (when appropriate)

❌ **Don't:**
- Write tests that depend on other tests
- Use `time.sleep()` for timing
- Test implementation details
- Skip tests without good reason
- Hardcode test data when fixtures exist

**See [docs/TESTING.md](docs/TESTING.md) for comprehensive testing guide.**

---

## Code Quality Standards

### Automated Checks

All code must pass these checks (runs in CI):

1. **ruff** - Python linter
2. **black** - Code formatter
3. **isort** - Import sorting
4. **mypy** - Type checking
5. **pytest** - All tests pass
6. **coverage** - >70% code coverage

### Running Checks Locally

```bash
# All linters (matches CI exactly)
make lint

# Individual checks
make lint-ruff
make lint-black
make lint-isort
make lint-mypy

# Auto-fix formatting issues
make format
```

### Type Hints

**Required** on all function signatures:

```python
# ✅ Good
def calculate_cost(power: float, rate: float) -> float:
    return power * rate

# ❌ Bad (missing type hints)
def calculate_cost(power, rate):
    return power * rate
```

### Documentation

**Docstrings required** for:
- All public functions and methods
- All classes
- All modules

**Use Google-style docstrings:**

```python
def example_function(param1: str, param2: int) -> bool:
    """
    One-line summary of function.

    More detailed description of what the function does,
    any important details, and usage examples.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
        KeyError: When param1 is not found

    Example:
        >>> example_function("test", 42)
        True
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")

    # Implementation...
```

---

## Submitting Changes

### Pull Request Process

1. **Ensure all checks pass locally:**
   ```bash
   make lint
   ./scripts/test-local.sh
   ```

2. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request** on GitHub:
   - Use a clear, descriptive title
   - Reference related issues (`Closes #123`)
   - Describe what changed and why
   - Include test results and screenshots if relevant
   - Mark as draft if work in progress

4. **Respond to review feedback:**
   - Address all comments
   - Push updates to the same branch
   - Mark conversations as resolved

### Pull Request Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to break)
- [ ] Documentation update

## Testing

- [ ] All existing tests pass
- [ ] Added new tests for changes
- [ ] Manual testing performed

## Checklist

- [ ] Code follows project style guidelines
- [ ] Added/updated docstrings
- [ ] Added/updated tests
- [ ] Updated documentation (if needed)
- [ ] Verified in local Docker environment
- [ ] All CI checks pass

## Related Issues

Closes #123
Related to #456
```

---

## Review Process

### What Reviewers Look For

1. **Correctness**
   - Does the code do what it claims?
   - Are edge cases handled?
   - Are there potential bugs?

2. **Test Coverage**
   - Are tests comprehensive?
   - Do tests cover error cases?
   - Is coverage >70%?

3. **Code Quality**
   - Is code readable and maintainable?
   - Are names descriptive?
   - Is complexity reasonable?

4. **Documentation**
   - Are docstrings complete?
   - Is behavior clear?
   - Are examples provided?

5. **Security**
   - Are inputs validated?
   - Are credentials handled securely?
   - Are there SQL injection risks?

### Review Timeline

- **Initial review:** Within 2-3 business days
- **Follow-up reviews:** Within 1-2 business days
- **Merge:** After approval from 1+ maintainers

### Getting Help

**Stuck or have questions?**

- Comment on your PR
- Ask in GitHub Discussions
- Join Discord server (link in README)
- Check [CLAUDE.md](CLAUDE.md) for AI assistant guidelines

---

## Community

### Communication Channels

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and general discussion
- **Discord** - Real-time chat with community
- **Email** - security@aetherlens.dev (security issues only)

### Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` (added automatically)
- Release notes
- Project documentation

---

## License

By contributing, you agree that your contributions will be licensed under the **MIT License**.

---

## Questions?

**Not sure about something?**

1. Check existing issues and discussions
2. Review [CLAUDE.md](CLAUDE.md) for development guidelines
3. Ask in GitHub Discussions
4. Reach out on Discord

**We appreciate all contributions, no matter how small!**

Thank you for helping make AetherLens better! 🚀
