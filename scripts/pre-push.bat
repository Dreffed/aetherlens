@echo off
REM Pre-push hook for Windows - runs comprehensive checks before pushing to remote
REM This ensures that code pushed to GitHub will pass CI checks
REM
REM Installation:
REM   scripts\install-hooks.bat
REM Or manually:
REM   copy scripts\pre-push.bat .git\hooks\pre-push
REM   (No .bat extension in .git\hooks\)

setlocal enabledelayedexpansion

echo [36m================================================[0m
echo [36mRunning pre-push checks...[0m
echo [36m================================================[0m
echo.

set SHOULD_PUSH=1

REM Step 1: Run ruff linting
echo =====================================================================
echo 1/5 Running ruff linter...
echo =====================================================================
.\venv\Scripts\python -m ruff check src/ tests/
if errorlevel 1 (
    echo [31m[ERROR] Ruff linting failed[0m
    echo [33m  Fix with: .\venv\Scripts\python -m ruff check src/ tests/ --fix[0m
    set SHOULD_PUSH=0
) else (
    echo [32m[OK] Ruff linting passed[0m
)

REM Step 2: Check black formatting
echo.
echo =====================================================================
echo 2/5 Checking black formatting...
echo =====================================================================
.\venv\Scripts\python -m black --check src/ tests/
if errorlevel 1 (
    echo [31m[ERROR] Black formatting failed[0m
    echo [33m  Fix with: .\venv\Scripts\python -m black src/ tests/[0m
    set SHOULD_PUSH=0
) else (
    echo [32m[OK] Black formatting passed[0m
)

REM Step 3: Check isort import ordering
echo.
echo =====================================================================
echo 3/5 Checking isort import ordering...
echo =====================================================================
.\venv\Scripts\python -m isort --check-only src/ tests/
if errorlevel 1 (
    echo [31m[ERROR] isort import ordering failed[0m
    echo [33m  Fix with: .\venv\Scripts\python -m isort src/ tests/[0m
    set SHOULD_PUSH=0
) else (
    echo [32m[OK] isort import ordering passed[0m
)

REM Step 4: Run unit tests
echo.
echo =====================================================================
echo 4/5 Running unit tests...
echo =====================================================================
.\venv\Scripts\pytest tests/unit/ -v --tb=short
if errorlevel 1 (
    echo [31m[ERROR] Unit tests failed[0m
    echo [33m  Fix tests before pushing[0m
    set SHOULD_PUSH=0
) else (
    echo [32m[OK] Unit tests passed[0m
)

REM Step 5: Run security tests
echo.
echo =====================================================================
echo 5/5 Running security tests...
echo =====================================================================
.\venv\Scripts\pytest tests/security/ -v -m security
if errorlevel 1 (
    echo [31m[ERROR] Security tests failed[0m
    echo [33m  Fix security issues before pushing[0m
    set SHOULD_PUSH=0
) else (
    echo [32m[OK] Security tests passed[0m
)

REM Step 6: Check test coverage (warning only)
echo.
echo =====================================================================
echo Bonus: Checking test coverage...
echo =====================================================================
echo Running coverage analysis (this may take a moment)...
.\venv\Scripts\pytest tests/unit/ tests/security/ --cov=src/aetherlens --cov-report=term --cov-report=xml -q > coverage_output.tmp 2>&1

REM Try to extract coverage from the output
for /f "tokens=4 delims= " %%a in ('findstr /C:"TOTAL" coverage_output.tmp') do (
    set COVERAGE=%%a
    set COVERAGE=!COVERAGE:%%=!
)

if defined COVERAGE (
    echo Current coverage: !COVERAGE!%%
    REM Note: batch doesn't do float comparison easily, so we just report it
    echo [32m[OK] Coverage report generated[0m
) else (
    echo [33m[WARNING] Could not calculate coverage[0m
)

del coverage_output.tmp 2>nul

REM Final summary
echo.
echo =====================================================================
if !SHOULD_PUSH! equ 1 (
    echo [32m[OK] All pre-push checks passed! Pushing to remote...[0m
    echo.
    exit /b 0
) else (
    echo.
    echo [31m[ERROR] Pre-push checks failed![0m
    echo.
    echo Please fix the issues above before pushing.
    echo.
    echo Quick fixes:
    echo   - Format code:  .\venv\Scripts\python -m black src/ tests/
    echo   - Format code:  .\venv\Scripts\python -m isort src/ tests/
    echo   - Run tests:    .\venv\Scripts\pytest tests/unit/ -v
    echo.
    echo To skip this check (NOT RECOMMENDED):
    echo   git push --no-verify
    echo.
    exit /b 1
)
