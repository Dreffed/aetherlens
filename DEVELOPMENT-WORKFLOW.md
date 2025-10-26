# Development Workflow - Preventing CI Failures

This guide shows **exactly what steps to follow** to prevent errors from reaching GitHub Actions.

## ⚠️ Problem: Errors Reaching GitHub

**Symptoms:**
- Local tests pass
- Push to GitHub
- CI fails with lint/test errors

**Root Cause:**
- Pre-push hook not running all CI checks
- Missing mypy type checking locally
- Not formatting code before committing

## ✅ Solution: Complete Workflow

Follow this workflow for **every change** to ensure CI passes:

### 1. Setup (One Time)

```cmd
REM Install git hooks
scripts\install-hooks.bat

REM Verify hooks are installed
dir .git\hooks\pre-push
```

### 2. Development Cycle

#### **Before Each Commit:**

```cmd
REM 1. Format your code (REQUIRED)
scripts\format.bat

REM 2. Review the changes
git diff

REM 3. Stage and commit
git add .
git commit -m "your message"
```

**Why format first?**
- Prevents formatting failures in pre-push hook
- Saves time - auto-fixes issues immediately
- Matches what CI will check

#### **Before Each Push:**

The pre-push hook **automatically runs** when you `git push`. It checks:

1. ✅ Ruff linting
2. ✅ Black formatting
3. ✅ isort import ordering
4. ✅ **mypy type checking** (NEW!)
5. ✅ Unit tests (all must pass)
6. ✅ Security tests
7. ℹ️ Coverage report (warning only)

**If pre-push fails:**

```cmd
REM See what failed in the output

REM Fix formatting issues
scripts\format.bat

REM Fix type errors
REM (Check mypy output for specific errors)

REM Fix failing tests
.\venv\Scripts\pytest tests/unit/ -v

REM Try pushing again
git push origin your-branch
```

### 3. Quick Reference

| Step | Command | When | Required? |
|------|---------|------|-----------|
| Format code | `scripts\format.bat` | Before commit | ✅ YES |
| Run tests | `.\venv\Scripts\pytest tests/unit/ -v` | Before commit | ✅ YES |
| Commit | `git commit -m "msg"` | After formatting | ✅ YES |
| Push | `git push` | After commit | ✅ YES |

## 🚨 CI Checks vs Local Checks

### What CI Runs (GitHub Actions):

```yaml
Lint Job:
  - ruff check src/ tests/
  - black --check src/ tests/
  - isort --check-only src/ tests/
  - mypy src/                      # Type checking

Unit Tests:
  - pytest tests/unit/ -v
  - Coverage check (>45%)

Integration Tests:
  - pytest tests/integration/ tests/api/
  - (Failures allowed in Phase 1)

Security Tests:
  - pytest tests/security/ -v -m security

Quality Tests:
  - pytest tests/quality/ -v -m quality
  - (Empty in Phase 1 - allowed)
```

### What Pre-Push Hook Runs (Local):

```cmd
1. ruff check src/ tests/
2. black --check src/ tests/
3. isort --check-only src/ tests/
4. mypy src/                       # ← ADDED (matches CI)
5. pytest tests/unit/ -v
6. pytest tests/security/ -v -m security
7. Coverage report (warning only)
```

**Now matches CI exactly!** ✅

## 🔧 Troubleshooting

### "Pre-push hook taking too long"

The hook runs all tests - this is intentional to catch errors early.

**Speed it up:**
```cmd
REM Run only specific tests during development
.\venv\Scripts\pytest tests/unit/test_config.py -v

REM Full pre-push check before pushing
git push
```

### "Mypy errors I don't understand"

```cmd
REM Run mypy locally to see errors
.\venv\Scripts\python -m mypy src/

REM Common fixes:
REM - Add type hints: def func(x: str) -> int:
REM - Import types: from typing import List, Dict, Optional
REM - Use Any for complex types: from typing import Any
```

### "Hook says tests pass but CI fails"

**Check for:**
1. **Uncommitted files** - Did you commit all changes?
   ```cmd
   git status
   ```

2. **Environment differences** - CI uses Python 3.11 & 3.12
   ```cmd
   python --version
   ```

3. **Missing dependencies**
   ```cmd
   pip install -r requirements-dev.txt
   ```

### "Integration tests failing locally"

Integration tests need Docker running:

```cmd
REM Check Docker status
docker ps

REM Start services
docker-compose up -d

REM Run integration tests
.\venv\Scripts\pytest tests/integration/ -v
```

**Note:** Integration test failures are **allowed** in Phase 1 CI (endpoints not implemented).

## 📋 Daily Workflow Example

```cmd
REM 1. Pull latest changes
git pull origin master

REM 2. Create feature branch
git checkout -b feature/my-feature

REM 3. Make your changes
code src/aetherlens/...

REM 4. Format code (do this OFTEN)
scripts\format.bat

REM 5. Run relevant tests
.\venv\Scripts\pytest tests/unit/test_myfeature.py -v

REM 6. Commit (formatted already!)
git add .
git commit -m "feat: add my feature"

REM 7. Push (pre-push hook runs automatically)
git push origin feature/my-feature
```

**If push fails:**
```cmd
REM Check what failed
REM Fix the issue
scripts\format.bat
git add .
git commit -m "fix: resolve lint/test issues"
git push
```

## ⚡ Pro Tips

### 1. Format Before Every Commit

```cmd
REM Add this to your muscle memory:
scripts\format.bat && git add . && git commit -m "your message"
```

### 2. Run Tests for Changed Files Only

```cmd
REM Faster feedback during development
.\venv\Scripts\pytest tests/unit/test_config.py -v
```

### 3. Check What Will Fail Before Pushing

```cmd
REM Manually run the pre-push script
scripts\pre-push.bat

REM This is what git push will run
```

### 4. Use VSCode Tasks

See WINDOWS-SETUP.md for VSCode integration with keyboard shortcuts.

## 🎯 Success Criteria

**Your push will succeed if:**

- ✅ `scripts\format.bat` shows "Code formatted successfully"
- ✅ `scripts\pre-push.bat` shows "All pre-push checks passed"
- ✅ All tests in `tests/unit/` pass
- ✅ No mypy type errors in `src/`
- ✅ Coverage stays above 45%

**Follow these steps and CI will always pass!** 🎉

## 📚 Related Documentation

- [WINDOWS-SETUP.md](WINDOWS-SETUP.md) - Windows setup and commands
- [CONTRIBUTING.md](CONTRIBUTING.md) - Full contribution guidelines
- [plans/github-actions-fix-plan.md](plans/github-actions-fix-plan.md) - CI fix details
