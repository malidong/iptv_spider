# IPTV Spider Agent Guidelines

## Code Style

- **Python 3.11+** required—use modern type hints (PEP 604: `str | None`, generics like `dict[str, list[obj]]`)
- **Memory-efficient classes**: Use `__slots__` for large objects (see [channel.py](../src/iptv_spider/channel.py#L1))
- **Linting**: Follow flake8 rules via `nox -s lint`; style violations block CI
- **No format configuration files** (no black, isort, prettier) — follow PEP 8 conventions

## Architecture

IPTV Spider filters and optimizes M3U8 playlists via speed testing:

- **[M3U8](../src/iptv_spider/m3u.py)** — Loads/parses playlists, applies regex filters, deduplication, and caching
- **[Channel](../src/iptv_spider/channel.py)** — Tests stream speeds, extracts metadata (resolution/FPS) via ffprobe
- **[main.py](../src/iptv_spider/main.py)** — Orchestrates workflow, outputs JSON and M3U files
- **[utils.py](../src/iptv_spider/utils.py)** — CLI argument parsing, config merging, path sanitization
- **[logger.py](../src/iptv_spider/logger.py)** — Dual logging (file + console) to `~/.iptv-spider/logs/`

**Workflow**: Load M3U8 → Filter by regex → Deduplicate → Speed test (parallel) → Cache results → Output best streams

See [README.md](../README.md#-features) for user-facing feature overview.

## Build and Test

| Task | Command | Notes |
|------|---------|-------|
| **Install** | `pip install .` or `pip install -e .` | Editable for development |
| **Run** | `iptv-spider` or `python -m iptv_spider` | Full CLI with `--help` |
| **Test** | `nox -s tests` | Runs pytest across Python 3.11–3.14 |
| **Lint** | `nox -s lint` | Flake8 style checks (required, no errors/warnings) |
| **Build Check** | `nox -s build_and_check_dists` | Validates packaging (PyPI-ready) |
| **Docker** | `docker build -t iptv-spider .` | Alpine-based, includes ffmpeg |

All `nox` sessions require dependencies in venv; see [setup.sh](../setup.sh) / [setup.ps1](../setup.ps1) for quick venv bootstrap.

## Key Conventions & Gotchas

**Config Precedence**: CLI args override env vars override hardcoded `RUNTIME_DEFAULTS`. No config file loading—all defaults are code-embedded.

**ffmpeg Requirement**: Speed tests and metadata extraction require `ffprobe`; Docker provides it. Local development must have ffmpeg installed.

**Cache Defaults**: Speed test results cached 24 hours in `~/.iptv-spider/tested_channels.json` via `--cache_enabled` (default true). Use `--cache_clear` to flush.

**Speed Constants**: Default threshold 0.3 MB/s, speed limit 2 MB/s—tuned for real-world streaming. Probe timeout 10s per channel to avoid hanging.

**Regex Patterns**: Default filter matches `CCTV-[1-17]` and `CCTV-5+`. Custom patterns passed via `--filter` must be valid Python regex; always anchor word boundaries with `\b` to avoid substring matches.

**Deduplication**: Only `dedup_keep="first"` currently implemented; "best" is stubbed.

**Concurrent Testing**: Uses ThreadPoolExecutor for parallel speed tests; thread count scales with channel volume.

## Development Workflow

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Git flow (dev/main, feat/fix/chore/hotfix/release branches)
- Issue-to-branch naming rule
- PR and release process
- Required quality gates (tests, lint, packaging, review approval)

**Quick start**: `git checkout -b feat/<issue>-<short-name>` from `dev` → implement → push → PR to `dev`.
