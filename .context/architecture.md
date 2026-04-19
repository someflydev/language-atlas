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
src/app/core/   build_sqlite.py   — JSON → SQLite pipeline
                data_loader.py    — unified SQLite/JSON access layer
                auditor.py        — AtlasAuditor (schema + referential integrity)
                insights.py       — InsightGenerator (window-function CTEs)
                site_builder.py   — SiteBuilder (Markdown → generated-docs/);
                                    SiteCrawler (static HTML export → site/)
                docs_parser.py    — legacy one-shot script; parses a now-deleted
                                    CONCEPTS.md into data/core_concepts.json.
                                    Not imported by any live module.
src/app/app.py  FastAPI routes + Jinja2 templates
src/app/templates/  Jinja2 HTML templates
src/cli.py      Typer CLI (atlas dashboard, odyssey, auto-odyssey)
src/tui.py      Textual TUI (LivingAtlasApp)
```

## Generated and Legacy Artifacts
```
generated-docs/     Markdown tree produced by `make docs` (SiteBuilder).
                    Gitignored; rebuilt on demand. Not read by the live app.
data/core_concepts.json  Output of docs_parser.py (legacy). Not loaded by
                         build_sqlite.py or data_loader.py. Safe to ignore.
```

## Data Flow
```
JSON + data/docs/ → build_sqlite.py → language_atlas.sqlite
                                            ↓
                               DataLoader (USE_SQLITE=1)
                                            ↓
               FastAPI /routes  |  CLI commands  |  TUI panels
```

## Client-Side SQLite Layer

The static export in `site/` includes a JavaScript shim
(`src/app/static/atlas-static.js`) that loads the project's SQLite
database in the browser using
[phiresky/sql.js-httpvfs](https://github.com/phiresky/sql.js-httpvfs).
The library uses HTTP range requests to fetch only the 4 KiB SQLite
pages needed for each query, making the published site fast even for
multi-megabyte databases. The database asset is copied to
`site/db/atlas/db.sqlite3` by `scripts/prep_pages.py` as part of the
`make pages` build step. See `GH_PAGES.md` for the full deploy
workflow.

## Key Design Choices
- `USE_SQLITE=1` env var activates SQLite mode in DataLoader; `0` reads JSON (used during build)
- `language_atlas.sqlite` is gitignored; rebuilt via `make build`
- All analytics use SQLite window functions and recursive CTEs (no pandas aggregations)
- FTS5 virtual table `search_index` powers `/search` and `/api/search`
- Auto-linking: `auto_link_content()` in app.py wraps known entity names in HTML links
- Static export: `SiteCrawler` uses `TestClient` to mirror live FastAPI output into `site/`.
  The crawler sets `ATLAS_STATIC_MODE=1` before importing the app so templates inject a
  "static export" notice. Internal links are rewritten to relative paths by `_rewrite_links`.
  `site/` is gitignored on `main`; the gh-pages branch deploy workflow is in `GH_PAGES.md`.
