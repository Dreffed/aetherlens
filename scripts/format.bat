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
    echo [ERROR] Must run from project root directory
    exit /b 1
)

echo Auto-formatting code...
echo.

REM 1. Run ruff with auto-fix
echo [1/3] Running ruff (with --fix)...
.\venv\Scripts\python -m ruff check src/ tests/ --fix
if errorlevel 1 (
    echo [WARNING] Ruff found some issues (some may be fixed)
) else (
    echo [OK] Ruff passed
)
echo.

REM 2. Run black
echo [2/3] Running black formatter...
.\venv\Scripts\python -m black src/ tests/
if errorlevel 1 (
    echo [ERROR] Black failed
    exit /b 1
) else (
    echo [OK] Black formatting applied
)
echo.

REM 3. Run isort
echo [3/3] Running isort import sorter...
.\venv\Scripts\python -m isort src/ tests/
if errorlevel 1 (
    echo [ERROR] isort failed
    exit /b 1
) else (
    echo [OK] Imports sorted
)
echo.

echo ========================================
echo [OK] Code formatted successfully!
echo ========================================
echo.
echo Next steps:
echo   1. Review changes: git diff
echo   2. Run tests: scripts\test-local.bat
echo   3. Commit: git add . ^&^& git commit -m "your message"
echo.

exit /b 0
