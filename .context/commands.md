# Commands & Operations

## Environment Setup
```bash
uv venv --python 3.12   # create venv (always specify version)
uv sync                  # install dependencies from uv.lock
```

## Development Server
```bash
make server
```

## Makefile Targets
| Target | Command |
|---|---|
| `make init` | Create venv, install deps, build database |
| `make build` | Rebuild SQLite from JSON: `PYTHONPATH=src uv run python -m app.core.build_sqlite` |
| `make server` | Start FastAPI dev server on port 8084 |
| `make audit` | Data integrity: `PYTHONPATH=src uv run python -m app.core.auditor` |
| `make dark-matter` | Missing profiles: `python3 scripts/dark_matter_audit.py` |
| `make test` | `pytest -v --cov=src/app/core` |
| `make harden` | type-check + audit + test |
| `make type-check` | `mypy . --config-file mypy.ini` |
| `make test-intensive` | `pytest -m intensive` |
| `make docs` | Generate Markdown docs: `PYTHONPATH=src uv run python -m app.core.site_builder` |
| `make site` | Build static HTML export into `site/`: `PYTHONPATH=src uv run python -m app.core.site_builder --html` |
| `make pages` | Prepare gh-pages artifacts (must be run on gh-pages branch): `python3 scripts/prep_pages.py` |
| `make clean` | Remove generated-docs/, dist/, build_temp/ |

## CLI (Typer — `src/cli.py`)
```bash
uv run atlas dashboard Python        # Control Room view for a language
uv run atlas paradigm Functional     # Paradigm ecosystem with ranked foundations
uv run atlas influences Scala        # Grouped upstream lineage + downstream influence
uv run atlas odyssey systems_renaissance  # Run a guided learning path
uv run atlas auto-odyssey "C"        # Dynamic lineage-based odyssey
# atlas --help for full command list
```

Notes:
- `atlas dashboard` and `atlas influences` now distinguish foundational precursors from direct language ancestors when grouped lineage data is available.
- `atlas paradigm` is the terminal entry point for the foundation-aware paradigm ecosystem introduced in the shared data layer.

## TUI (`src/tui.py`)
```bash
uv run python3 src/tui.py   # Launch Textual TUI (LivingAtlasApp)
# Press 'o' to toggle Odyssey mode inside TUI
# Press 'm' to cycle chronology browse mode: languages, foundations, artifacts, all
```

## Scripts
| Script | Purpose |
|---|---|
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
