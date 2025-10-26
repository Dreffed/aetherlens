@echo off
REM Auto-format code with black, isort, and ruff
REM Matches the formatting done by pre-commit hooks

setlocal enabledelayedexpansion

echo ========================================
echo   AetherLens Code Formatter
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo [31m[ERROR] Must run from project root directory[0m
    exit /b 1
)

echo Auto-formatting code...
echo.

REM 1. Run ruff with auto-fix
echo [1/3] Running ruff (with --fix)...
.\venv\Scripts\python -m ruff check src/ tests/ --fix
if errorlevel 1 (
    echo [33m[WARNING] Ruff found some issues (some may be fixed)[0m
) else (
    echo [32m[OK] Ruff passed[0m
)
echo.

REM 2. Run black
echo [2/3] Running black formatter...
.\venv\Scripts\python -m black src/ tests/
if errorlevel 1 (
    echo [31m[ERROR] Black failed[0m
    exit /b 1
) else (
    echo [32m[OK] Black formatting applied[0m
)
echo.

REM 3. Run isort
echo [3/3] Running isort import sorter...
.\venv\Scripts\python -m isort src/ tests/
if errorlevel 1 (
    echo [31m[ERROR] isort failed[0m
    exit /b 1
) else (
    echo [32m[OK] Imports sorted[0m
)
echo.

echo ========================================
echo [32m[OK] Code formatted successfully![0m
echo ========================================
echo.
echo Next steps:
echo   1. Review changes: git diff
echo   2. Run tests: scripts\test-local.bat
echo   3. Commit: git add . ^&^& git commit -m "your message"
echo.

exit /b 0
