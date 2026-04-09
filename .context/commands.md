# Commands & Operations

## Environment Setup
```bash
uv venv --python 3.12   # create venv (always specify version)
uv sync                  # install dependencies from uv.lock
```

## Development Server
```bash
# From repo root:
cd src/app && uv run uvicorn app:app --reload --port 8084
# Or via Makefile (if make server target exists):
make server
```

## Makefile Targets
| Target | Command |
|---|---|
| `make build` | Rebuild SQLite from JSON: `python3 src/app/core/build_sqlite.py` |
| `make docs` | Generate Markdown docs (including INDEX.md and README.md): `uv run python scripts/generate_docs.py` |
| `make audit` | Data integrity: `python3 src/app/core/auditor.py` |
| `make dark-matter` | Missing profiles: `python3 scripts/dark_matter_audit.py` |
| `make test` | `pytest -v --cov=src/app/core` |
| `make test-intensive` | `pytest -m intensive` |
| `make type-check` | `mypy . --config-file mypy.ini` |
| `make harden` | type-check + audit + test |
| `make clean` | Remove generated-docs/, dist/, build_temp/ |

## CLI (Typer — `src/cli.py`)
```bash
uv run atlas dashboard Python        # Control Room view for a language
uv run atlas odyssey systems_renaissance  # Run a guided learning path
uv run atlas auto-odyssey "C"        # Dynamic lineage-based odyssey
# atlas --help for full command list
```

## TUI (`src/tui.py`)
```bash
uv run python3 src/tui.py   # Launch Textual TUI (LivingAtlasApp)
# Press 'o' to toggle Odyssey mode inside TUI
```

## Scripts
| Script | Purpose |
|---|---|
| `scripts/generate_docs.py` | Generate Markdown in generated-docs/ from SQLite |
| `scripts/generate_reports.py` | JSON analytics reports in generated-reports/ |
| `scripts/dark_matter_audit.py` | Find missing profiles, writes dark_matter_todo.json |
| `scripts/audit_lineage.py` | Lineage integrity check |
| `scripts/check_integrity.py` | Data integrity verification |
| `scripts/data_stats.py` | Summary stats |
| `scripts/inspect_sqlite.py` | SQLite schema inspection |
| `scripts/db_query.py` | Ad-hoc SQL queries |
| `scripts/export_summary.py` | Export summary data |
| `scripts/build_zenith.py` | Build self-contained binary (PyInstaller) |
| `scripts/atlas-fuzzy.sh` | Fuzzy shell search helper |

## pytest Configuration
- `testpaths = ["tests"]`
- `pythonpath = ["src"]`
- `addopts = "--strict-markers --cov=src/app/core"`
- Test files: `tests/test_auditor.py`, `test_data_loader_full.py`, `test_data_parity.py`, `test_hardening.py`, `test_insights.py`, `test_paradigm_significance.py`
