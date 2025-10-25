# AetherLens Makefile
# Provides convenient commands for development, testing, and linting

.PHONY: help install install-dev lint format test test-unit test-integration test-api test-performance test-coverage clean docker-test pre-commit-install

# Default target
help:
	@echo "AetherLens Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install              Install production dependencies"
	@echo "  make install-dev          Install development dependencies"
	@echo "  make pre-commit-install   Install pre-commit hooks"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run all linters (matches GitHub Actions)"
	@echo "  make format               Auto-format code with black, isort, ruff"
	@echo "  make lint-ruff            Run ruff linter"
	@echo "  make lint-black           Check black formatting"
	@echo "  make lint-isort           Check isort import ordering"
	@echo "  make lint-mypy            Run mypy type checking"
	@echo "  make lint-security        Run security checks (bandit, safety)"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run all tests"
	@echo "  make test-unit            Run unit tests only"
	@echo "  make test-integration     Run integration tests"
	@echo "  make test-api             Run API tests"
	@echo "  make test-performance     Run performance tests"
	@echo "  make test-coverage        Run tests with coverage report"
	@echo "  make docker-test          Run tests in Docker environment"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                Remove build artifacts and cache files"
	@echo "  make db-migrate           Run database migrations"
	@echo "  make db-backup            Backup database"
	@echo ""

# Installation
install:
	pip install -e .

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

pre-commit-install:
	pip install pre-commit
	pre-commit install
	@echo "Pre-commit hooks installed successfully!"

# Linting (matches GitHub Actions CI exactly)
lint:
	@echo "Running all linters (matching GitHub Actions)..."
	@echo ""
	@echo "1/4 Running ruff..."
	ruff check src/ tests/
	@echo ""
	@echo "2/4 Running black..."
	black --check src/ tests/
	@echo ""
	@echo "3/4 Running isort..."
	isort --check-only src/ tests/
	@echo ""
	@echo "4/4 Running mypy..."
	mypy src/
	@echo ""
	@echo "✓ All linters passed!"

lint-ruff:
	ruff check src/ tests/

lint-black:
	black --check src/ tests/

lint-isort:
	isort --check-only src/ tests/

lint-mypy:
	mypy src/

lint-security:
	@echo "Running security checks..."
	safety check || true
	bandit -r src/ -f screen

# Code Formatting (auto-fix)
format:
	@echo "Auto-formatting code..."
	ruff check src/ tests/ --fix
	black src/ tests/
	isort src/ tests/
	@echo "✓ Code formatted!"

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ tests/api/ -v -m "integration or not performance"

test-api:
	pytest tests/api/ -v

test-performance:
	pytest tests/performance/ -v -m performance

test-coverage:
	pytest tests/ -v --cov=src/aetherlens --cov-report=html --cov-report=term
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Docker-based testing
docker-test:
	@echo "Running tests in Docker environment..."
	docker-compose -f docker/docker-compose.test.yml up -d db-test redis-test
	@echo "Waiting for services..."
	@sleep 5
	docker-compose -f docker/docker-compose.test.yml exec -T db-test pg_isready -U postgres || true
	@echo "Running tests..."
	DATABASE_URL="postgresql://postgres:test_password@localhost:5433/aetherlens_test" \
	REDIS_URL="redis://localhost:6380/0" \
	SECRET_KEY="test_secret_key_minimum_32_characters_long" \
	pytest tests/ -v --cov=src/aetherlens --cov-report=term
	@echo "Cleaning up..."
	docker-compose -f docker/docker-compose.test.yml down -v

# Database operations
db-migrate:
	@echo "Running database migrations..."
	docker-compose -f docker/docker-compose.yml exec -T db psql -U postgres -d aetherlens -f /docker-entrypoint-initdb.d/01-enable-timescaledb.sql || true
	@for file in migrations/versions/*.sql; do \
		echo "Running $$file..."; \
		docker-compose -f docker/docker-compose.yml exec -T db psql -U postgres -d aetherlens -f /migrations/versions/$$(basename $$file); \
	done
	@echo "✓ Migrations complete!"

db-backup:
	bash scripts/backup_database.sh

# Cleanup
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleanup complete!"
