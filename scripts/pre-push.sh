#!/bin/bash
# Pre-push hook - runs comprehensive checks before pushing to remote
# This ensures that code pushed to GitHub will pass CI checks
#
# Installation:
#   ./scripts/install-hooks.sh
# Or manually:
#   cp scripts/pre-push.sh .git/hooks/pre-push
#   chmod +x .git/hooks/pre-push

set -e  # Exit on any error

echo "🔍 Running pre-push checks..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if we should push
SHOULD_PUSH=true

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_step() {
    echo ""
    echo "====================================================================="
    echo "$1"
    echo "====================================================================="
}

# Step 1: Run ruff linting
print_step "1/5 Running ruff linter..."
if ruff check src/ tests/; then
    print_status "$GREEN" "✓ Ruff linting passed"
else
    print_status "$RED" "✗ Ruff linting failed"
    print_status "$YELLOW" "  Fix with: ruff check src/ tests/ --fix"
    SHOULD_PUSH=false
fi

# Step 2: Check black formatting
print_step "2/5 Checking black formatting..."
if black --check src/ tests/; then
    print_status "$GREEN" "✓ Black formatting passed"
else
    print_status "$RED" "✗ Black formatting failed"
    print_status "$YELLOW" "  Fix with: black src/ tests/"
    SHOULD_PUSH=false
fi

# Step 3: Check isort import ordering
print_step "3/5 Checking isort import ordering..."
if isort --check-only src/ tests/; then
    print_status "$GREEN" "✓ isort import ordering passed"
else
    print_status "$RED" "✗ isort import ordering failed"
    print_status "$YELLOW" "  Fix with: isort src/ tests/"
    SHOULD_PUSH=false
fi

# Step 4: Run unit tests
print_step "4/5 Running unit tests..."
if pytest tests/unit/ -v --tb=short; then
    print_status "$GREEN" "✓ Unit tests passed"
else
    print_status "$RED" "✗ Unit tests failed"
    print_status "$YELLOW" "  Fix tests before pushing"
    SHOULD_PUSH=false
fi

# Step 5: Run security tests
print_step "5/5 Running security tests..."
if pytest tests/security/ -v -m security; then
    print_status "$GREEN" "✓ Security tests passed"
else
    print_status "$RED" "✗ Security tests failed"
    print_status "$YELLOW" "  Fix security issues before pushing"
    SHOULD_PUSH=false
fi

# Step 6: Check test coverage (warning only, doesn't block)
print_step "Bonus: Checking test coverage..."
echo "Running coverage analysis (this may take a moment)..."
if COVERAGE_OUTPUT=$(pytest tests/unit/ tests/security/ --cov=src/aetherlens --cov-report=term --cov-report=xml -q 2>&1); then
    # Extract coverage percentage from output
    COVERAGE=$(echo "$COVERAGE_OUTPUT" | grep "TOTAL" | awk '{print $4}' | tr -d '%')

    if [ -n "$COVERAGE" ]; then
        echo "Current coverage: ${COVERAGE}%"

        # Check if coverage is acceptable (45% threshold for now)
        if (( $(echo "$COVERAGE < 45.0" | bc -l) )); then
            print_status "$YELLOW" "⚠ Warning: Coverage is ${COVERAGE}% (below 45% threshold)"
            echo "This is not blocking, but consider adding more tests."
        else
            print_status "$GREEN" "✓ Coverage is ${COVERAGE}% (above 45% threshold)"
        fi
    fi
else
    print_status "$YELLOW" "⚠ Warning: Could not calculate coverage"
fi

# Final summary
echo ""
echo "====================================================================="
if [ "$SHOULD_PUSH" = true ]; then
    print_status "$GREEN" "✅ All pre-push checks passed! Pushing to remote..."
    echo ""
    exit 0
else
    echo ""
    print_status "$RED" "❌ Pre-push checks failed!"
    echo ""
    echo "Please fix the issues above before pushing."
    echo ""
    echo "Quick fixes:"
    echo "  - Format code:  make format"
    echo "  - Run tests:    pytest tests/unit/ -v"
    echo "  - Check lint:   make lint"
    echo ""
    echo "To skip this check (NOT RECOMMENDED):"
    echo "  git push --no-verify"
    echo ""
    exit 1
fi
