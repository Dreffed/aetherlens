@echo off
REM Install git hooks for AetherLens development
REM This script installs both pre-commit and pre-push hooks

setlocal

echo Installing git hooks for AetherLens...
echo.

REM Check if .git directory exists
if not exist ".git" (
    echo [31m[ERROR] Not in a git repository. Run this from the project root.[0m
    exit /b 1
)

REM Install pre-commit hooks using pre-commit package
echo 1/3 Installing pre-commit hooks...
where pre-commit >nul 2>&1
if %errorlevel% equ 0 (
    pre-commit install
    echo [32m[OK] Pre-commit hooks installed[0m
) else (
    echo [33m[WARNING] pre-commit not found. Install with: pip install pre-commit[0m
    echo            Then run: pre-commit install
)

echo.

REM Install pre-push hook
echo 2/3 Installing pre-push hook...
if exist ".git\hooks\pre-push" (
    echo   Backing up existing pre-push hook to pre-push.backup
    move /y .git\hooks\pre-push .git\hooks\pre-push.backup >nul
)

copy /y scripts\pre-push.bat .git\hooks\pre-push >nul
echo [32m[OK] Pre-push hook installed[0m

echo.

REM Configure git hooks
echo 3/3 Setting up hook configuration...
git config --local core.hooksPath .git/hooks
echo [32m[OK] Git hooks configured[0m

echo.
echo =====================================================================
echo [32m[OK] All git hooks installed successfully![0m
echo =====================================================================
echo.
echo What happens now:
echo.
echo ON COMMIT (pre-commit):
echo   - Trailing whitespace removed
echo   - Files end with newline
echo   - YAML/JSON/TOML validated
echo   - Code auto-formatted (ruff, black, isort)
echo   - Type checking (mypy on src/)
echo   - Security scanning (bandit)
echo.
echo ON PUSH (pre-push):
echo   - Ruff linting
echo   - Black formatting check
echo   - isort import ordering
echo   - Unit tests
echo   - Security tests
echo   - Coverage report (warning only)
echo.
echo To skip hooks (NOT RECOMMENDED):
echo   git commit --no-verify
echo   git push --no-verify
echo.
echo To test the pre-push hook manually:
echo   scripts\pre-push.bat
echo.

endlocal
