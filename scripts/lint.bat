@echo off
REM Lint script for Windows that exactly matches GitHub Actions CI
REM This ensures local linting produces the same results as CI

setlocal enabledelayedexpansion

echo ========================================
echo   AetherLens Linting (matches CI)
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo Error: Must run from project root directory
    exit /b 1
)

set FAILED=0

REM 1. Run ruff
echo [1/4] Running ruff linter...
call ruff check src/ tests/
if errorlevel 1 (
    echo X ruff failed
    set FAILED=1
) else (
    echo + ruff passed
)
echo.

REM 2. Run black
echo [2/4] Running black formatter check...
call black --check src/ tests/
if errorlevel 1 (
    echo X black failed
    echo Tip: Run 'make format' or 'black src/ tests/' to auto-fix
    set FAILED=1
) else (
    echo + black passed
)
echo.

REM 3. Run isort
echo [3/4] Running isort import check...
call isort --check-only src/ tests/
if errorlevel 1 (
    echo X isort failed
    echo Tip: Run 'make format' or 'isort src/ tests/' to auto-fix
    set FAILED=1
) else (
    echo + isort passed
)
echo.

REM 4. Run mypy
echo [4/4] Running mypy type checker...
call mypy src/
if errorlevel 1 (
    echo X mypy failed
    set FAILED=1
) else (
    echo + mypy passed
)
echo.

REM Summary
echo ========================================
if %FAILED%==0 (
    echo + All linting checks passed!
    echo   Ready to push to GitHub
    echo ========================================
    exit /b 0
) else (
    echo X Some linting checks failed
    echo.
    echo To auto-fix formatting issues, run:
    echo   make format
    echo.
    echo Or manually fix with:
    echo   black src/ tests/
    echo   isort src/ tests/
    echo   ruff check src/ tests/ --fix
    echo ========================================
    exit /b 1
)
