# Windows Setup Guide (Without Make)

This guide provides Windows-native commands for developers without `make` installed.

## Quick Setup

### 1. Install Git Hooks

```cmd
REM Run from project root
scripts\install-hooks.bat
```

This installs both pre-commit and pre-push hooks.

## Common Development Commands

### Code Quality

```cmd
REM Run all linters (matches GitHub Actions)
.\venv\Scripts\python -m ruff check src/ tests/
.\venv\Scripts\python -m black --check src/ tests/
.\venv\Scripts\python -m isort --check-only src/ tests/
.\venv\Scripts\python -m mypy src/

REM Auto-format code
.\venv\Scripts\python -m ruff check src/ tests/ --fix
.\venv\Scripts\python -m black src/ tests/
.\venv\Scripts\python -m isort src/ tests/
```

### Testing

```cmd
REM Run all tests
.\venv\Scripts\pytest tests/ -v

REM Run unit tests only
.\venv\Scripts\pytest tests/unit/ -v

REM Run with coverage
.\venv\Scripts\pytest tests/ -v --cov=src/aetherlens --cov-report=html --cov-report=term

REM Run security tests
.\venv\Scripts\pytest tests/security/ -v -m security
```

### Pre-Push Checks

```cmd
REM Run the same checks that will run on git push
scripts\pre-push.bat
```

### Documentation

```cmd
REM Format markdown files
.\venv\Scripts\mdformat plans/ docs/ *.md

REM Check markdown formatting
.\venv\Scripts\mdformat --check plans/ docs/ *.md
```

## Batch Script Alternatives

Instead of `make` commands, use these batch scripts:

| Make Command            | Windows Alternative          | Description                           |
| ----------------------- | ---------------------------- | ------------------------------------- |
| `make install-hooks`    | `scripts\install-hooks.bat`  | Install pre-commit + pre-push hooks   |
| `make pre-push`         | `scripts\pre-push.bat`       | Run pre-push validation               |
| `make lint`             | `scripts\lint.bat`           | Run all linters (matches CI)          |
| `make format`           | `scripts\format.bat`         | Auto-format code                      |
| `make test`             | `scripts\test-local.bat`     | Run all tests                         |

All these scripts are already created and ready to use!

## Git Workflow (Windows)

### Daily Development

```cmd
REM 1. Make changes to code

REM 2. Format code
scripts\format.bat

REM 3. Run tests
.\venv\Scripts\pytest tests/unit/ -v

REM 4. Commit changes
git add .
git commit -m "feat: your feature"

REM 5. Push (pre-push hooks run automatically)
git push origin your-branch
```

### Before Pushing

```cmd
REM Test locally before pushing
scripts\pre-push.bat

REM If all checks pass, push
git push origin your-branch
```

### If Pre-Push Fails

```cmd
REM Fix formatting
scripts\format.bat

REM Fix tests
.\venv\Scripts\pytest tests/unit/ -v

REM Try again
git push origin your-branch
```

## Troubleshooting

### Python Not Found

```cmd
REM Make sure virtual environment is activated
.\venv\Scripts\activate

REM Or use full path
.\venv\Scripts\python -m pytest tests/ -v
```

### Permission Denied

```cmd
REM Run as administrator or check file permissions
icacls scripts\*.bat /grant %username%:F
```

### Git Hooks Not Running

**Error: "cannot spawn .git/hooks/pre-push: No such file or directory"**

This means the pre-push hook isn't installed. Run:

```cmd
scripts\install-hooks.bat
```

The install script creates a bash wrapper that Git for Windows can execute. To verify:

```cmd
REM Check if hook exists
dir .git\hooks\pre-push

REM Test the hook manually
.git\hooks\pre-push
```

### Skip Hooks (Emergency Only)

```cmd
REM Skip pre-commit hooks
git commit --no-verify -m "message"

REM Skip pre-push hooks
git push --no-verify
```

## Visual Studio Code Integration

Add these tasks to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Format Code",
      "type": "shell",
      "command": ".\\venv\\Scripts\\python",
      "args": ["-m", "black", "src/", "tests/"],
      "group": "build"
    },
    {
      "label": "Run Linters",
      "type": "shell",
      "command": "scripts\\lint.bat",
      "group": "test"
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": ".\\venv\\Scripts\\pytest",
      "args": ["tests/", "-v"],
      "group": "test"
    },
    {
      "label": "Pre-Push Checks",
      "type": "shell",
      "command": "scripts\\pre-push.bat",
      "group": "test"
    }
  ]
}
```

Then run with: `Ctrl+Shift+B` → Select task

## PowerShell Alternatives

If you prefer PowerShell:

```powershell
# Format code
& .\venv\Scripts\python -m black src/ tests/
& .\venv\Scripts\python -m isort src/ tests/

# Run tests
& .\venv\Scripts\pytest tests/ -v

# Run pre-push checks
& .\scripts\pre-push.bat
```

## Install Make (Optional)

If you want to use `make` commands:

### Option 1: Chocolatey

```cmd
choco install make
```

### Option 2: WSL (Windows Subsystem for Linux)

```cmd
wsl --install
# Then use make in WSL
```

### Option 3: Git Bash

Make is included with Git for Windows. Use Git Bash:

```bash
# In Git Bash
make install-hooks
make pre-push
```

## Summary

**Key Windows Commands:**

```cmd
# Setup (one time)
scripts\install-hooks.bat

# Before each push
scripts\pre-push.bat

# Daily development
scripts\format.bat
.\venv\Scripts\pytest tests/unit/ -v
```

That's it! No `make` required.
