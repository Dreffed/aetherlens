# Development Guide

This guide covers setting up your development environment for AetherLens Home Edition.

## Prerequisites

- Python 3.11 or higher
- Docker Desktop (for running services)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/aetherlens/home.git
cd home
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

### 3. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and update values (especially SECRET_KEY)
```

### 4. Start Development Services

```bash
# Start TimescaleDB and Redis
cd docker
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

### 5. Initialize Database

```bash
# Run migrations (once implemented)
# alembic upgrade head
```

### 6. Run Development Server

```bash
# Start server with hot reload
python -m uvicorn aetherlens.api.main:app --reload --log-level debug
```

The API will be available at http://localhost:8080

## Development Workflow

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/

# Or use pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/aetherlens --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py

# Run tests matching pattern
pytest -k "test_authentication"
```

### Docker Development

```bash
# Start all services including dev tools
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Access services:
# - API: http://localhost:8080
# - PGAdmin: http://localhost:5050 (admin@aetherlens.local / admin)
# - Redis Commander: http://localhost:8081

# View logs
docker-compose logs -f aetherlens

# Rebuild containers
docker-compose build --no-cache
```

## Project Structure

```
aetherlens/
├── src/aetherlens/          # Main application code
│   ├── api/                 # FastAPI routes and endpoints
│   ├── models/              # Data models
│   ├── plugins/             # Plugin system
│   ├── collection/          # Metric collection
│   ├── costs/               # Cost calculation
│   ├── security/            # Authentication & security
│   └── config.py            # Configuration
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── docker/                  # Docker configuration
├── .github/workflows/       # CI/CD pipelines
└── docs/                    # Documentation
```

## Common Tasks

### Adding a New Dependency

```bash
# Add to requirements.txt or requirements-dev.txt
echo "new-package==1.0.0" >> requirements.txt

# Install
pip install -r requirements.txt

# Update locked versions
pip freeze > requirements.lock
```

### Creating a Database Migration

```bash
# Create migration
alembic revision -m "description of changes"

# Edit the generated file in migrations/versions/

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Debugging

```bash
# Use ipdb for debugging
pip install ipdb

# In your code:
import ipdb; ipdb.set_trace()

# Or use VS Code debugger with launch.json
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Pylance
- Ruff
- Even Better TOML
- Docker

### PyCharm

1. Mark `src` as Sources Root
2. Enable Django/FastAPI support
3. Configure pytest as test runner
4. Enable mypy and ruff inspections

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8080
# Windows:
netstat -ano | findstr :8080
# Linux/macOS:
lsof -i :8080

# Kill the process or change port in .env
```

### Database Connection Issues

```bash
# Check if TimescaleDB is running
docker-compose ps timescaledb

# Check logs
docker-compose logs timescaledb

# Restart service
docker-compose restart timescaledb
```

### Import Errors

```bash
# Ensure PYTHONPATH includes src/
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# Or install in editable mode
pip install -e .
```

## Resources

- [Architecture Documentation](./ARCHITECTURE.md)
- [API Documentation](./INTERFACES.md)
- [Coding Standards](./CLAUDE.md)
- [Database Schema](./SCHEMA.md)

## Getting Help

- GitHub Discussions: https://github.com/aetherlens/home/discussions
- Discord: https://discord.gg/aetherlens
- Issues: https://github.com/aetherlens/home/issues
