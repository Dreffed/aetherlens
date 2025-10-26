#!/bin/bash
# Install git hooks for AetherLens development
# This script installs both pre-commit and pre-push hooks

set -e

echo "Installing git hooks for AetherLens..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .git directory exists
if [ ! -d ".git" ]; then
    echo "Error: Not in a git repository. Run this from the project root."
    exit 1
fi

# Install pre-commit hooks using pre-commit package
echo "1/3 Installing pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
else
    echo -e "${YELLOW}⚠ pre-commit not found. Install with: pip install pre-commit${NC}"
    echo "   Then run: pre-commit install"
fi

echo ""

# Install pre-push hook
echo "2/3 Installing pre-push hook..."
if [ -f ".git/hooks/pre-push" ]; then
    echo "  Backing up existing pre-push hook to pre-push.backup"
    mv .git/hooks/pre-push .git/hooks/pre-push.backup
fi

cp scripts/pre-push.sh .git/hooks/pre-push
chmod +x .git/hooks/pre-push
echo -e "${GREEN}✓ Pre-push hook installed${NC}"

echo ""

# Create a commit-msg hook reminder (optional)
echo "3/3 Setting up hook configuration..."
git config --local core.hooksPath .git/hooks
echo -e "${GREEN}✓ Git hooks configured${NC}"

echo ""
echo "====================================================================="
echo -e "${GREEN}✓ All git hooks installed successfully!${NC}"
echo "====================================================================="
echo ""
echo "What happens now:"
echo ""
echo "ON COMMIT (pre-commit):"
echo "  - Trailing whitespace removed"
echo "  - Files end with newline"
echo "  - YAML/JSON/TOML validated"
echo "  - Code auto-formatted (ruff, black, isort)"
echo "  - Type checking (mypy on src/)"
echo "  - Security scanning (bandit)"
echo ""
echo "ON PUSH (pre-push):"
echo "  - Ruff linting"
echo "  - Black formatting check"
echo "  - isort import ordering"
echo "  - Unit tests"
echo "  - Security tests"
echo "  - Coverage report (warning only)"
echo ""
echo "To skip hooks (NOT RECOMMENDED):"
echo "  git commit --no-verify"
echo "  git push --no-verify"
echo ""
echo "To test the pre-push hook manually:"
echo "  ./scripts/pre-push.sh"
echo ""
