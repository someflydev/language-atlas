# Architecture

## Stack
- **Runtime:** Python 3.12, managed with `uv`
- **Web:** FastAPI + Jinja2 (port 8084), HTMX for partials
- **CLI:** Typer + Rich (`src/cli.py`)
- **TUI:** Textual (`src/tui.py`)
- **Data:** SQLite (primary runtime) | JSON files (source of truth)
- **Viz:** Plotly Express + NetworkX; Polars for transforms, Pandas/PyArrow bridge to Plotly

## Layers
```
data/           JSON source of truth (languages, paradigms, people, etc.)
data/docs/      Rich narrative profiles (language_profiles/, concept_profiles/, etc.)
src/app/core/   build_sqlite.py | data_loader.py | auditor.py | insights.py
                site_builder.py  (Markdown generation for generated-docs/)
src/app/app.py  FastAPI routes + Jinja2 templates
src/app/templates/  Jinja2 HTML templates
src/cli.py      Typer CLI (atlas dashboard, odyssey, auto-odyssey)
src/tui.py      Textual TUI (LivingAtlasApp)
```

## Data Flow
```
JSON + data/docs/ → build_sqlite.py → language_atlas.sqlite
                                            ↓
                               DataLoader (USE_SQLITE=1)
                                            ↓
               FastAPI /routes  |  CLI commands  |  TUI panels
```

## Key Design Choices
- `USE_SQLITE=1` env var activates SQLite mode in DataLoader; `0` reads JSON (used during build)
- `language_atlas.sqlite` is gitignored; rebuilt via `make build`
- All analytics use SQLite window functions and recursive CTEs (no pandas aggregations)
- FTS5 virtual table `search_index` powers `/search` and `/api/search`
- Auto-linking: `auto_link_content()` in app.py wraps known entity names in HTML links
