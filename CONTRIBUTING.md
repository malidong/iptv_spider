# Contributing Guide

## Branching Model

- `main`: release and pre-release only. No direct feature development.
- `dev`: integration branch for day-to-day development.
- `feat/<issue-number>-<short-name>`: new features from `dev`, merge back to `dev`.
- `fix/<issue-number>-<short-name>`: bug fixes from `dev`, merge back to `dev`.
- `chore/<issue-number>-<short-name>`: maintenance tasks from `dev`, merge back to `dev`.
- `hotfix/<version>`: urgent production fixes from `main`, merge back to both `main` and `dev`.
- `release/<version>`: release hardening branch from `dev`, merge to `main` after verification.

## Issue-to-Branch Rule

- One issue should map to one branch.
- Branch names should include the issue number.
- Every PR should reference its issue in the description, for example:
  - `Fixes #123`
  - `Refs #123`

## Pull Request Flow

1. Create issue and put it in the project board.
2. Create branch from `dev`.
3. Implement and push.
4. Open PR to `dev`.
5. Wait for CI + review approval.
6. Squash merge into `dev`.

## Release Flow

1. When milestone scope on `dev` is complete, create `release/<version>` from `dev`.
2. Only stabilization, docs, and release notes changes are allowed on release branch.
3. Merge release branch to `main`.
4. Tag and publish release/pre-release from `main`.
5. Back-merge any post-release fixes to `dev`.

## Required Quality Gates

- Tests must pass in GitHub Actions.
- Lint must pass.
- Packaging checks must pass.
- At least one reviewer approval is required.

## Local Development

### Pre-commit Checks

Before committing or pushing, run local checks to avoid CI failures:

```powershell
# Windows PowerShell
pwsh -File scripts/pre-commit-check.ps1

# Unix/Mac
bash scripts/pre-commit-check.sh
```

The script will:
1. Check if `uv` is installed (required)
2. Install flake8 and pytest (if not installed)
3. Run lint check with flake8
4. Run all tests with pytest
5. Exit with error if any check fails

### Manual Commands

If you prefer running commands directly:

```bash
# Install dependencies
uv pip install flake8 pytest

# Run lint
uv run flake8 src/ tests/

# Run tests
uv run pytest tests/ -v
```

### Requirements

- [uv](https://github.com/astral-sh/uv) must be installed
- All checks must pass before `git commit` or `git push`

