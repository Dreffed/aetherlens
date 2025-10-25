#!/bin/bash
# Local testing script with Docker services
# This script matches the GitHub Actions CI environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RUN_MIGRATIONS=true
RUN_COVERAGE=true
TEST_CATEGORY="all"
CLEANUP=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-migrations)
            RUN_MIGRATIONS=false
            shift
            ;;
        --no-coverage)
            RUN_COVERAGE=false
            shift
            ;;
        --no-cleanup)
            CLEANUP=false
            shift
            ;;
        --unit)
            TEST_CATEGORY="unit"
            shift
            ;;
        --integration)
            TEST_CATEGORY="integration"
            shift
            ;;
        --api)
            TEST_CATEGORY="api"
            shift
            ;;
        --performance)
            TEST_CATEGORY="performance"
            shift
            ;;
        --security)
            TEST_CATEGORY="security"
            shift
            ;;
        --quality)
            TEST_CATEGORY="quality"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-migrations    Skip database migrations"
            echo "  --no-coverage      Skip coverage reporting"
            echo "  --no-cleanup       Don't cleanup containers after tests"
            echo "  --unit             Run only unit tests"
            echo "  --integration      Run only integration tests"
            echo "  --api              Run only API tests"
            echo "  --performance      Run only performance tests"
            echo "  --security         Run only security tests"
            echo "  --quality          Run only code quality tests"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================"
echo "  AetherLens Local Test Suite"
echo "========================================${NC}"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi

# Step 1: Start test services
echo -e "${BLUE}[1/6] Starting test services...${NC}"
docker-compose -f docker/docker-compose.test.yml up -d db-test redis-test

# Step 2: Wait for services to be healthy
echo -e "${BLUE}[2/6] Waiting for services to be healthy...${NC}"
echo -n "  Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker-compose -f docker/docker-compose.test.yml exec -T db-test pg_isready -U postgres &> /dev/null; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e " ${RED}✗ Timeout${NC}"
        docker-compose -f docker/docker-compose.test.yml logs db-test
        exit 1
    fi
    sleep 1
    echo -n "."
done

echo -n "  Waiting for Redis..."
for i in {1..30}; do
    if docker-compose -f docker/docker-compose.test.yml exec -T redis-test redis-cli ping &> /dev/null; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e " ${RED}✗ Timeout${NC}"
        docker-compose -f docker/docker-compose.test.yml logs redis-test
        exit 1
    fi
    sleep 1
    echo -n "."
done

# Step 3: Run database migrations
if [ "$RUN_MIGRATIONS" = true ]; then
    echo -e "${BLUE}[3/6] Running database migrations...${NC}"

    # Enable TimescaleDB
    docker-compose -f docker/docker-compose.test.yml exec -T db-test \
        psql -U postgres -d aetherlens_test -f /docker-entrypoint-initdb.d/01-enable-timescaledb.sql 2>/dev/null || true

    # Run migrations
    for file in migrations/versions/*.sql; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            echo "  Running migration: $filename"
            docker-compose -f docker/docker-compose.test.yml exec -T db-test \
                psql -U postgres -d aetherlens_test < "$file"
        fi
    done
    echo -e "${GREEN}  Migrations complete${NC}"
else
    echo -e "${YELLOW}[3/6] Skipping migrations${NC}"
fi

# Step 4: Run tests
echo -e "${BLUE}[4/6] Running tests...${NC}"

# Set environment variables
export DATABASE_URL="postgresql://postgres:test_password@localhost:5433/aetherlens_test"
export REDIS_URL="redis://localhost:6380/0"
export SECRET_KEY="test_secret_key_minimum_32_characters_long_for_testing_only"
export PYTHONPATH="${PWD}/src"

# Determine test path and markers
case $TEST_CATEGORY in
    unit)
        TEST_PATH="tests/unit/"
        MARKERS=""
        echo "  Running unit tests only"
        ;;
    integration)
        TEST_PATH="tests/integration/ tests/api/"
        MARKERS='-m "integration or not performance"'
        echo "  Running integration and API tests"
        ;;
    api)
        TEST_PATH="tests/api/"
        MARKERS=""
        echo "  Running API tests only"
        ;;
    performance)
        TEST_PATH="tests/performance/"
        MARKERS="-m performance"
        echo "  Running performance tests only"
        ;;
    security)
        TEST_PATH="tests/security/"
        MARKERS="-m security"
        echo "  Running security tests only"
        ;;
    quality)
        TEST_PATH="tests/quality/"
        MARKERS="-m quality"
        echo "  Running code quality tests only"
        ;;
    all)
        TEST_PATH="tests/"
        MARKERS="-m 'not performance'"
        echo "  Running all tests (excluding performance)"
        ;;
esac

# Build pytest command
PYTEST_CMD="pytest $TEST_PATH -v"

if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src/aetherlens --cov-report=html --cov-report=term --cov-report=xml"
fi

if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD $MARKERS"
fi

# Run tests
echo ""
eval $PYTEST_CMD
TEST_EXIT_CODE=$?

# Step 5: Show coverage summary
if [ "$RUN_COVERAGE" = true ] && [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${BLUE}[5/6] Coverage summary:${NC}"
    echo "  HTML report: htmlcov/index.html"
    echo "  XML report:  coverage.xml"
else
    echo -e "${YELLOW}[5/6] Skipping coverage report${NC}"
fi

# Step 6: Cleanup
if [ "$CLEANUP" = true ]; then
    echo -e "${BLUE}[6/6] Cleaning up test environment...${NC}"
    docker-compose -f docker/docker-compose.test.yml down -v
    echo -e "${GREEN}  Cleanup complete${NC}"
else
    echo -e "${YELLOW}[6/6] Leaving test environment running${NC}"
    echo "  To cleanup later, run:"
    echo "  docker-compose -f docker/docker-compose.test.yml down -v"
fi

# Final summary
echo ""
echo -e "${BLUE}========================================${NC}"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo -e "${BLUE}========================================${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo -e "${BLUE}========================================${NC}"
    exit $TEST_EXIT_CODE
fi
