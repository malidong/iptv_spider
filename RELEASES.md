# Release Readiness Checklist v0.5.0

## Pre-Release DoD (Definition of Done)

### Code Quality
- [x] All 106 tests pass
- [x] Lint passes (flake8)
- [x] No security vulnerabilities (CodeQL)
- [x] Documentation updated (README, CHANGELOG, RELEASES.md)

### Test Matrix Status
- [x] Python 3.11 - PASSED
- [x] Python 3.12 - PASSED
- [x] Python 3.13 - PASSED
- [x] Python 3.14 - PASSED
- [x] Ubuntu - PASSED
- [x] macOS - PASSED
- [x] Windows - PASSED

### CI Pipeline
- [x] Test workflow - PASSED
- [x] Release Verify workflow - PASSED
- [x] PR Guard - PASSED
- [x] OpenCode Review - APPROVED

### Release Artifact Integrity
- [x] Package builds successfully (`python -m build`)
- [x] Container builds successfully (`docker build`)
- [x] Container runs health check (`iptv-spider --health`)
- [x] All dependencies declared in pyproject.toml

### v0.5.0 Milestone Issues (14/15 completed)
- [x] #2 Container baseline (Dockerfile + compose + volume contracts)
- [x] #3 Unified config layer (CLI > ENV > defaults)
- [x] #4 FFprobe integration
- [x] #5 Quality Score v1
- [x] #6 Smart deduplication
- [x] #7 Templated export engine
- [x] #8 Custom API sync exporter
- [x] #9 Cron scheduler
- [x] #10 Resilience improvements
- [x] #11 Observability baseline
- [x] #12 CI pipeline updates
- [x] #13 Documentation refresh
- [x] #14 Release checklist (this PR)
- [ ] #15 Roadmap tracking (continuous task)
- [x] #10 Resilience improvements
- [x] #11 Observability baseline
- [x] #12 CI pipeline updates
- [x] #13 Documentation refresh
- [ ] #14 Release checklist (this issue)

### Configuration Changes
| Feature | CLI Flag | Env Var | Default |
|--------|--------|--------|--------|
| Health Check | `--health` | - | False |
| Verbose | `--verbose` | - | False |
| Cron Schedule | - | `IPTV_SPIDER_CRON_SCHEDULE` | - |
| Lock File | - | `IPTV_SPIDER_LOCK_FILE` | `.iptv_spider.lock` |
| Cache Clear | `--cache_clear` | - | False |
| Network Check | - | `IPTV_HEALTH_CHECK_NETWORK` | True |

### New Package Dependencies
- `m3u8==6.0.0`
- `requests==2.32.3`

### Rollback Steps
1. Revert to previous release tag: `git checkout v0.4.0`
2. Re-install previous version: `pip install iptv-spider==0.4.0`
3. Rollback container image if used
4. Restore previous configuration

### Post-Release Tasks
- [ ] Tag release: `git tag -a v0.5.0 -m "Release v0.5.0"`
- [ ] Push tag: `git push origin v0.5.0`
- [ ] Create GitHub release with release notes
- [ ] Publish to PyPI (automatic via release.yml)
- [ ] Update Docker Hub image if applicable
- [ ] Announce in channels

---

## v0.4.0 → v0.5.0 Migration

### Breaking Changes
None - v0.5.0 is fully backward compatible with v0.4.0.

### New Features
- Health check command: `iptv-spider --health`
- Structured logging with run IDs
- Cron scheduler with lock mechanism for preventing overlapping runs
- Template export (Docker Compose, custom)
- Quality Score (rule-based channel ranking)
- Smart deduplication (URL fingerprint)
- Error tracking (RunStats, RunError)
- Observability baseline (structured logs, health checks)

### Upgrade Steps
```bash
# Update package
pip install --upgrade iptv-spider

# Or rebuild container
docker build -t iptv-spider:latest .
```