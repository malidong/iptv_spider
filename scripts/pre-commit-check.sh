#!/usr/bin/env bash
# Run local checks before commit/push
# Usage: ./scripts/pre-commit-check.sh

set -e

echo "========================================"
echo "Running Local Pre-commit Checks"
echo "========================================"

echo ""
echo "1. Installing dependencies..."
uv pip install flake8 pytest --quiet

echo ""
echo "2. Running lint check..."
uv run flake8 src/ tests/ --exclude=.venv
echo "   ✓ Lint passed"

echo ""
echo "3. Running tests..."
uv run pytest tests/ -v --tb=short
echo "   ✓ Tests passed"

echo ""
echo "========================================"
echo "All checks passed! Ready to commit."
echo "========================================"