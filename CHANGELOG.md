# Changelog

## v0.5.0 - 2026-04-19

### New Features
- Health check command (`--health`, `--verbose`)
- Structured logging with run IDs for observability
- Cron scheduler with lock mechanism to prevent overlapping runs
- Template export engine (Docker Compose, custom templates)
- Custom API sync exporter (push mode)
- Quality Score v1 (rule-based channel ranking)
- Smart deduplication v1 (URL fingerprint)
- Resilience improvements (retry, backoff, error categorization)
- CI pipeline for packaging and container verification

### Configuration
- New CLI flags: `--health`, `--verbose`, `--cache_clear`
- New env vars: `IPTV_SPIDER_CRON_SCHEDULE`, `IPTV_SPIDER_LOCK_FILE`, `IPTV_HEALTH_CHECK_NETWORK`
- Unified config layer: CLI > ENV > defaults hierarchy

### Bug Fixes
- Various test coverage improvements
- Documentation refresh

### Dependencies
- m3u8==6.0.0
- requests==2.32.3

---

## v0.4.0 - 2026-03-22

- Add EPG header support in M3U output (optional `url-tvg`)
- Add URL fingerprint deduplication and incremental speed cache
- Add cache maintenance with TTL purge and `--cache_clear`
- Update CLI parameters, tests, and docs (EN/ZH)