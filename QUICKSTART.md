# Quick Start Guide

## TL;DR - Get Started in 5 Minutes

```bash
# 1. Setup
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .

# 2. Install pre-commit hooks (prevents bad commits)
pip install pre-commit
pre-commit install

# 3. Before every commit/push
./venv/Scripts/ruff check src/ tests/
./venv/Scripts/black --check src/ tests/
./venv/Scripts/isort --check-only src/ tests/
./venv/Scripts/mypy src/

# Or auto-fix formatting:
./venv/Scripts/black src/ tests/
./venv/Scripts/isort src/ tests/
./venv/Scripts/ruff check src/ tests/ --fix

# 4. Run tests
./venv/Scripts/pytest tests/ -v
```

## For Make Users (Linux/Mac)

```bash
make install-dev          # Install dependencies
make pre-commit-install   # Setup hooks
make lint                 # Check code quality (matches CI)
make format               # Auto-fix formatting
make test                 # Run all tests
```

## Common Commands

| Task                    | Command (Windows)                                                                                                                                                                                              | Command (Linux/Mac with Make) |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| **Check before push**   | `.\venv\Scripts\python -m ruff check src/ tests/`<br>`.\venv\Scripts\python -m black --check src/ tests/`<br>`.\venv\Scripts\python -m isort --check-only src/ tests/`<br>`.\venv\Scripts\python -m mypy src/` | `make lint`                   |
| **Auto-fix formatting** | `.\venv\Scripts\python -m black src/ tests/`<br>`.\venv\Scripts\python -m isort src/ tests/`<br>`.\venv\Scripts\python -m ruff check src/ tests/ --fix`                                                        | `make format`                 |
| **Run tests**           | `.\venv\Scripts\pytest tests/ -v`                                                                                                                                                                              | `make test`                   |
| **Test coverage**       | `.\venv\Scripts\pytest tests/ -v --cov=src/aetherlens`                                                                                                                                                         | `make test-coverage`          |

## What Runs in GitHub Actions CI?

These exact commands run on every push/PR:

```bash
# Linting
ruff check src/ tests/
black --check src/ tests/
isort --check-only src/ tests/
mypy src/

# Testing
pytest tests/ -v --cov=src/aetherlens
```

**Run these locally before pushing to avoid CI failures!**

## Pre-Commit Hooks

After running `pre-commit install`, these run automatically on `git commit`:

- ✅ Ruff linting (auto-fixes issues)
- ✅ Black formatting (auto-fixes)
- ✅ isort import sorting (auto-fixes)
- ✅ mypy type checking
- ✅ Security checks (bandit)
- ✅ File checks (trailing whitespace, EOF, etc.)

**If hooks fail, fix issues and commit again.**

## Workflow

```bash
# 1. Make changes
vim src/aetherlens/api/main.py

# 2. Test your changes
./venv/Scripts/pytest tests/unit/ -v

# 3. Check code quality
./venv/Scripts/ruff check src/ tests/
./venv/Scripts/black --check src/ tests/
./venv/Scripts/isort --check-only src/ tests/
./venv/Scripts/mypy src/

# 4. If formatting issues, auto-fix
./venv/Scripts/black src/ tests/
./venv/Scripts/isort src/ tests/
./venv/Scripts/ruff check src/ tests/ --fix

# 5. Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: your feature"

# 6. Push
git push origin your-branch
```

## Full Documentation

- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Complete development guide
- **[TESTING.md](docs/TESTING.md)** - Testing documentation
- **[API.md](docs/API.md)** - API documentation
- **[CLAUDE.md](CLAUDE.md)** - AI assistant guidelines

## Need Help?

- 📖 Read [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed instructions
- 🐛 Found a bug? [Create an issue](https://github.com/aetherlens/home/issues)
- 💬 Questions? [GitHub Discussions](https://github.com/aetherlens/home/discussions)
