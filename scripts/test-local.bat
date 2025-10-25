@echo off
REM Local testing script with Docker services for Windows
REM This script matches the GitHub Actions CI environment

setlocal enabledelayedexpansion

set RUN_MIGRATIONS=true
set RUN_COVERAGE=true
set TEST_CATEGORY=all
set CLEANUP=true

REM Parse arguments
:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--no-migrations" (
    set RUN_MIGRATIONS=false
    shift
    goto parse_args
)
if "%~1"=="--no-coverage" (
    set RUN_COVERAGE=false
    shift
    goto parse_args
)
if "%~1"=="--no-cleanup" (
    set CLEANUP=false
    shift
    goto parse_args
)
if "%~1"=="--unit" (
    set TEST_CATEGORY=unit
    shift
    goto parse_args
)
if "%~1"=="--integration" (
    set TEST_CATEGORY=integration
    shift
    goto parse_args
)
if "%~1"=="--api" (
    set TEST_CATEGORY=api
    shift
    goto parse_args
)
if "%~1"=="--performance" (
    set TEST_CATEGORY=performance
    shift
    goto parse_args
)
if "%~1"=="--security" (
    set TEST_CATEGORY=security
    shift
    goto parse_args
)
if "%~1"=="--quality" (
    set TEST_CATEGORY=quality
    shift
    goto parse_args
)
if "%~1"=="--help" (
    echo Usage: %0 [OPTIONS]
    echo.
    echo Options:
    echo   --no-migrations    Skip database migrations
    echo   --no-coverage      Skip coverage reporting
    echo   --no-cleanup       Don't cleanup containers after tests
    echo   --unit             Run only unit tests
    echo   --integration      Run only integration tests
    echo   --api              Run only API tests
    echo   --performance      Run only performance tests
    echo   --security         Run only security tests
    echo   --quality          Run only code quality tests
    echo   --help             Show this help message
    exit /b 0
)
echo Unknown option: %~1
echo Use --help for usage information
exit /b 1

:end_parse

echo ========================================
echo   AetherLens Local Test Suite
echo ========================================
echo.

REM Step 1: Start test services
echo [1/6] Starting test services...
docker-compose -f docker/docker-compose.test.yml up -d db-test redis-test

REM Step 2: Wait for services to be healthy
echo [2/6] Waiting for services to be healthy...
echo   Waiting for PostgreSQL...
timeout /t 5 /nobreak >nul
docker-compose -f docker/docker-compose.test.yml exec -T db-test pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
    echo   X PostgreSQL failed to start
    docker-compose -f docker/docker-compose.test.yml logs db-test
    exit /b 1
)
echo   + PostgreSQL ready

echo   Waiting for Redis...
timeout /t 2 /nobreak >nul
docker-compose -f docker/docker-compose.test.yml exec -T redis-test redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo   X Redis failed to start
    docker-compose -f docker/docker-compose.test.yml logs redis-test
    exit /b 1
)
echo   + Redis ready

REM Step 3: Run database migrations
if "%RUN_MIGRATIONS%"=="true" (
    echo [3/6] Running database migrations...

    REM Enable TimescaleDB
    docker-compose -f docker/docker-compose.test.yml exec -T db-test psql -U postgres -d aetherlens_test -f /docker-entrypoint-initdb.d/01-enable-timescaledb.sql >nul 2>&1

    REM Run migrations
    for %%f in (migrations\versions\*.sql) do (
        echo   Running migration: %%~nxf
        docker-compose -f docker/docker-compose.test.yml exec -T db-test psql -U postgres -d aetherlens_test < "%%f"
    )
    echo   + Migrations complete
) else (
    echo [3/6] Skipping migrations
)

REM Step 4: Run tests
echo [4/6] Running tests...

REM Set environment variables
set DATABASE_URL=postgresql://postgres:test_password@localhost:5433/aetherlens_test
set REDIS_URL=redis://localhost:6380/0
set SECRET_KEY=test_secret_key_minimum_32_characters_long_for_testing_only
set PYTHONPATH=%CD%\src

REM Determine test path and markers
if "%TEST_CATEGORY%"=="unit" (
    set TEST_PATH=tests/unit/
    set MARKERS=
    echo   Running unit tests only
) else if "%TEST_CATEGORY%"=="integration" (
    set TEST_PATH=tests/integration/ tests/api/
    set MARKERS=-m "integration or not performance"
    echo   Running integration and API tests
) else if "%TEST_CATEGORY%"=="api" (
    set TEST_PATH=tests/api/
    set MARKERS=
    echo   Running API tests only
) else if "%TEST_CATEGORY%"=="performance" (
    set TEST_PATH=tests/performance/
    set MARKERS=-m performance
    echo   Running performance tests only
) else if "%TEST_CATEGORY%"=="security" (
    set TEST_PATH=tests/security/
    set MARKERS=-m security
    echo   Running security tests only
) else if "%TEST_CATEGORY%"=="quality" (
    set TEST_PATH=tests/quality/
    set MARKERS=-m quality
    echo   Running code quality tests only
) else (
    set TEST_PATH=tests/
    set MARKERS=-m "not performance"
    echo   Running all tests (excluding performance)
)

REM Build pytest command
set PYTEST_CMD=pytest %TEST_PATH% -v

if "%RUN_COVERAGE%"=="true" (
    set PYTEST_CMD=%PYTEST_CMD% --cov=src/aetherlens --cov-report=html --cov-report=term --cov-report=xml
)

if not "%MARKERS%"=="" (
    set PYTEST_CMD=%PYTEST_CMD% %MARKERS%
)

REM Run tests
echo.
call %PYTEST_CMD%
set TEST_EXIT_CODE=%errorlevel%

REM Step 5: Show coverage summary
if "%RUN_COVERAGE%"=="true" (
    if %TEST_EXIT_CODE%==0 (
        echo.
        echo [5/6] Coverage summary:
        echo   HTML report: htmlcov\index.html
        echo   XML report:  coverage.xml
    )
) else (
    echo [5/6] Skipping coverage report
)

REM Step 6: Cleanup
if "%CLEANUP%"=="true" (
    echo [6/6] Cleaning up test environment...
    docker-compose -f docker/docker-compose.test.yml down -v
    echo   + Cleanup complete
) else (
    echo [6/6] Leaving test environment running
    echo   To cleanup later, run:
    echo   docker-compose -f docker/docker-compose.test.yml down -v
)

REM Final summary
echo.
echo ========================================
if %TEST_EXIT_CODE%==0 (
    echo + All tests passed!
    echo ========================================
    exit /b 0
) else (
    echo X Some tests failed
    echo ========================================
    exit /b %TEST_EXIT_CODE%
)
