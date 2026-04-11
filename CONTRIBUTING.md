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

