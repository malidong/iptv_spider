#!/usr/bin/env bash
# Pre-commit check script for Unix/Mac
# Run this before committing: bash scripts/pre-commit-check.sh

set -e

echo "========================================"
echo "Running Local Pre-commit Checks"
echo "========================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed." >&2
    echo "Please install uv from: https://github.com/astral-sh/uv" >&2
    exit 1
fi

echo "1. Installing dependencies..."
uv pip install flake8 pytest --quiet

echo ""
echo "2. Running lint check..."
uv run flake8 src/ tests/ --exclude=.venv
echo "   Lint passed"

echo ""
echo "3. Running tests..."
uv run pytest tests/ -v --tb=short
echo "   Tests passed"

echo ""
echo "========================================"
echo "All checks passed! Ready to commit."
echo "========================================"