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

echo ================================================
echo Running pre-push checks...
echo ================================================
echo.

set SHOULD_PUSH=1

REM Step 1: Run ruff linting
echo =====================================================================
echo 1/5 Running ruff linter...
echo =====================================================================
.\venv\Scripts\python -m ruff check src/ tests/
if errorlevel 1 (
    echo [ERROR] Ruff linting failed
    echo   Fix with: .\venv\Scripts\python -m ruff check src/ tests/ --fix
    set SHOULD_PUSH=0
) else (
    echo [OK] Ruff linting passed
)

REM Step 2: Check black formatting
echo.
echo =====================================================================
echo 2/5 Checking black formatting...
echo =====================================================================
.\venv\Scripts\python -m black --check src/ tests/
if errorlevel 1 (
    echo [ERROR] Black formatting failed
    echo   Fix with: .\venv\Scripts\python -m black src/ tests/
    set SHOULD_PUSH=0
) else (
    echo [OK] Black formatting passed
)

REM Step 3: Check isort import ordering
echo.
echo =====================================================================
echo 3/5 Checking isort import ordering...
echo =====================================================================
.\venv\Scripts\python -m isort --check-only src/ tests/
if errorlevel 1 (
    echo [ERROR] isort import ordering failed
    echo   Fix with: .\venv\Scripts\python -m isort src/ tests/
    set SHOULD_PUSH=0
) else (
    echo [OK] isort import ordering passed
)

REM Step 4: Run mypy type checking (warning only in Phase 1)
echo.
echo =====================================================================
echo 4/6 Running mypy type checking...
echo =====================================================================
.\venv\Scripts\python -m mypy src/
if errorlevel 1 (
    echo [WARNING] Type checking found errors (non-blocking in Phase 1)
    echo   These will need to be fixed before Phase 2
    echo   See output above for details
) else (
    echo [OK] Type checking passed
)

REM Step 5: Run unit tests
echo.
echo =====================================================================
echo 5/6 Running unit tests...
echo =====================================================================
.\venv\Scripts\pytest tests/unit/ -v --tb=short
if errorlevel 1 (
    echo [ERROR] Unit tests failed
    echo   Fix tests before pushing
    set SHOULD_PUSH=0
) else (
    echo [OK] Unit tests passed
)

REM Step 6: Run security tests
echo.
echo =====================================================================
echo 6/6 Running security tests...
echo =====================================================================
.\venv\Scripts\pytest tests/security/ -v -m security
if errorlevel 1 (
    echo [ERROR] Security tests failed
    echo   Fix security issues before pushing
    set SHOULD_PUSH=0
) else (
    echo [OK] Security tests passed
)

REM Bonus: Check test coverage (warning only)
echo.
echo =====================================================================
echo Bonus: Checking test coverage...
echo =====================================================================
echo Running coverage analysis (this may take a moment)...
.\venv\Scripts\pytest tests/unit/ tests/security/ --cov=src/aetherlens --cov-report=term --cov-report=xml -q > coverage_output.tmp 2>&1

REM Try to extract coverage from the output
set "COVERAGE="
for /f "tokens=4 delims= " %%a in ('findstr /C:"TOTAL" coverage_output.tmp') do (
    set "COVERAGE=%%a"
)

if defined COVERAGE (
    echo Current coverage: !COVERAGE!
    REM Note: batch doesn't do float comparison easily, so we just report it
    echo [OK] Coverage report generated
) else (
    echo [WARNING] Could not calculate coverage
)

del coverage_output.tmp 2>nul

REM Final summary
echo.
echo =====================================================================
if %SHOULD_PUSH% EQU 1 (
    echo.
    echo [OK] All pre-push checks passed! Pushing to remote...
    echo.
    exit /b 0
)

echo.
echo [ERROR] Pre-push checks failed!
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
