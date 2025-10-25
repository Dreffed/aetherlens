#!/bin/bash
# Lint script that exactly matches GitHub Actions CI
# This ensures local linting produces the same results as CI

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

echo "========================================"
echo "  AetherLens Linting (matches CI)"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Check if dependencies are installed
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        echo "Run: pip install -r requirements-dev.txt"
        exit 1
    fi
}

echo -e "${BLUE}Checking dependencies...${NC}"
check_command ruff
check_command black
check_command isort
check_command mypy
echo -e "${GREEN}✓ All dependencies installed${NC}"
echo ""

# 1. Run ruff (exactly as in CI)
echo -e "${BLUE}[1/4] Running ruff linter...${NC}"
if ruff check src/ tests/; then
    echo -e "${GREEN}✓ ruff passed${NC}"
else
    echo -e "${RED}✗ ruff failed${NC}"
    FAILED=1
fi
echo ""

# 2. Run black (exactly as in CI)
echo -e "${BLUE}[2/4] Running black formatter check...${NC}"
if black --check src/ tests/; then
    echo -e "${GREEN}✓ black passed${NC}"
else
    echo -e "${RED}✗ black failed${NC}"
    echo -e "${YELLOW}Tip: Run 'make format' or 'black src/ tests/' to auto-fix${NC}"
    FAILED=1
fi
echo ""

# 3. Run isort (exactly as in CI)
echo -e "${BLUE}[3/4] Running isort import check...${NC}"
if isort --check-only src/ tests/; then
    echo -e "${GREEN}✓ isort passed${NC}"
else
    echo -e "${RED}✗ isort failed${NC}"
    echo -e "${YELLOW}Tip: Run 'make format' or 'isort src/ tests/' to auto-fix${NC}"
    FAILED=1
fi
echo ""

# 4. Run mypy (exactly as in CI)
echo -e "${BLUE}[4/4] Running mypy type checker...${NC}"
if mypy src/; then
    echo -e "${GREEN}✓ mypy passed${NC}"
else
    echo -e "${RED}✗ mypy failed${NC}"
    FAILED=1
fi
echo ""

# Summary
echo "========================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All linting checks passed!${NC}"
    echo -e "${GREEN}  Ready to push to GitHub${NC}"
    echo "========================================"
    exit 0
else
    echo -e "${RED}✗ Some linting checks failed${NC}"
    echo ""
    echo "To auto-fix formatting issues, run:"
    echo "  make format"
    echo ""
    echo "Or manually fix with:"
    echo "  black src/ tests/"
    echo "  isort src/ tests/"
    echo "  ruff check src/ tests/ --fix"
    echo "========================================"
    exit 1
fi
