@echo off
REM Pre-commit hook for Windows - auto-formats code before committing
REM This ensures code is always formatted correctly
REM
REM Installation:
REM   scripts\install-hooks.bat

setlocal enabledelayedexpansion

echo ================================================
echo Running pre-commit auto-formatting...
echo ================================================
echo.

set AUTO_FORMATTED=0

REM Step 1: Run ruff with auto-fix
echo =====================================================================
echo 1/3 Running ruff (with --fix)...
echo =====================================================================
.\venv\Scripts\python -m ruff check src/ tests/ --fix
if errorlevel 1 (
    echo [WARNING] Ruff found issues (attempting to fix)
    set AUTO_FORMATTED=1
) else (
    echo [OK] Ruff passed
)
echo.

REM Step 2: Run black auto-format
echo =====================================================================
echo 2/3 Running black formatter...
echo =====================================================================
.\venv\Scripts\python -m black src/ tests/
if errorlevel 1 (
    echo [ERROR] Black failed
    exit /b 1
)
echo [OK] Black formatting applied
set AUTO_FORMATTED=1
echo.

REM Step 3: Run isort
echo =====================================================================
echo 3/3 Running isort import sorter...
echo =====================================================================
.\venv\Scripts\python -m isort src/ tests/
if errorlevel 1 (
    echo [ERROR] isort failed
    exit /b 1
)
echo [OK] Imports sorted
set AUTO_FORMATTED=1
echo.

REM Check if files were modified
echo =====================================================================
if %AUTO_FORMATTED% EQU 1 (
    echo.
    echo [INFO] Code was auto-formatted
    echo.
    echo Next steps:
    echo   1. Review the changes: git diff
    echo   2. Stage the formatted files: git add .
    echo   3. Commit again: git commit
    echo.
) else (
    echo [OK] All files already formatted correctly!
)
echo =====================================================================

exit /b 0
