# Pre-commit check script for Windows
# Run this before committing: pwsh -File scripts/pre-commit-check.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Local Pre-commit Checks" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Installing dependencies..." -ForegroundColor Yellow
uv pip install flake8 pytest --quiet

Write-Host ""
Write-Host "2. Running lint check..." -ForegroundColor Yellow
uv run flake8 src/ tests/ --exclude=.venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "LINT FAILED - Fix errors before committing" -ForegroundColor Red
    exit 1
}
Write-Host "   Lint passed" -ForegroundColor Green

Write-Host ""
Write-Host "3. Running tests..." -ForegroundColor Yellow
uv run pytest tests/ -v --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-Host "TESTS FAILED - Fix failures before committing" -ForegroundColor Red
    exit 1
}
Write-Host "   Tests passed" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All checks passed! Ready to commit." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan