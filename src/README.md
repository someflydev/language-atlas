# src/ — Codebase Architecture

Language Atlas is a data-driven research platform for exploring the
history, evolution, and intellectual lineage of programming languages.
This document describes the source layout, modules, and operational
commands for contributors working in this directory.

## Module Overview

### Core logic (`src/app/core/`)

- **`data_loader.py`** — Unified data access layer. Reads from
  `language_atlas.sqlite` in normal operation (`USE_SQLITE=1`) and
  falls back to JSON files during the build step (`USE_SQLITE=0`).
  All routes and commands go through DataLoader; no module issues raw
  SQL except DataLoader and InsightGenerator.
- **`build_sqlite.py`** — Transforms the JSON source files into
  `language_atlas.sqlite`. Calculates `influence_score`, builds the
  FTS5 `search_index` virtual table, and creates analytical views.
  Run via `make build`.
- **`auditor.py`** — `AtlasAuditor`: validates JSON schema and
  referential integrity across all data files. Run via `make audit`.
- **`insights.py`** — `InsightGenerator`: window-function and
  recursive CTE queries used by the insights dashboard.
- **`site_builder.py`** — Two output modes:
  - `SiteBuilder`: generates the `generated-docs/` Markdown tree
    from DataLoader data. Run via `make docs`.
  - `SiteCrawler`: spins up the FastAPI app via `TestClient`, walks
    every exported GET route, and writes fully-rendered HTML to
    `site/`. Rewrites internal links to relative paths. Sets
    `ATLAS_STATIC_MODE=1` so templates inject a static-export notice.
    Run via `make site`.
- **`docs_parser.py`** — Legacy one-shot script that parsed a
  now-deleted `docs/CONCEPTS.md` into `data/core_concepts.json`.
  Not imported by any live module; safe to ignore.

### Web server (`src/app/app.py`)

FastAPI application serving all HTML and JSON routes on port 8084.
See `API_GUIDE.md` for the full endpoint reference and `.context/routes.md`
for the complete route-to-template map.

### CLI (`src/cli.py`)

Typer CLI exposing `atlas dashboard`, `atlas odyssey <id>`, and
`atlas auto-odyssey <language>`. Run with `uv run atlas --help`.

### TUI (`src/tui.py`)

Textual three-pane browser with real-time FTS5 search and an Odyssey
mode (toggle with `o`). Run with `uv run atlas tui`.

## Guided and Auto-generated Learning Paths (Odysseys)

Two kinds of learning paths exist:

- **Guided paths** (`data/learning_paths.json`): hand-curated sequences
  of languages with milestones and challenges (e.g., "The Systems
  Renaissance").
- **Auto-Odyssey**: generated at request time via a recursive CTE that
  walks the influence graph to find influential descendants of a
  starting language. Available at `/odyssey/auto` and via
  `atlas auto-odyssey`.

## JSON API

The server exposes a JSON API at `/api`. See `API_GUIDE.md` for all
endpoints. Interactive documentation is available at `/docs` (Swagger)
and `/redoc` while the server is running.

Notable endpoints:
- `GET /api/search?q=concurrency` — FTS5 BM25 ranked results
- `GET /api/language/Rust` — combined core + profile data
- `GET /api/odysseys` — list all guided paths
- `GET /visualizations` — Plotly timeline and influence network

## Data Architecture

- **Polars** handles backend data transformation, sorting, and
  aggregation before results are passed to routes.
- **SQLite (FTS5)** provides indexed full-text search and the
  relational query layer for all analytical features.
- **Plotly Express** renders visualizations, using a Pandas/PyArrow
  bridge to consume Polars DataFrames.

## Data Quality

```bash
make audit        # AtlasAuditor: schema + referential integrity
make dark-matter  # Missing-profile audit; writes generated-reports/dark_matter_todo.json
make harden       # type-check + audit + test in one step
```

The dark matter audit reads all source JSON and narrative profile dirs
under `data/docs/`. It uses a reviewed alias layer in two hidden files:

- `data/.dark_matter_aliases.json` — variant references to canonical terms
- `data/.dark_matter_canonicals.json` — canonical terms, entity types,
  and optional profile-stem overrides

## Common Commands

```bash
# Start the web server
make server

# Start a guided Odyssey in the CLI
uv run atlas odyssey systems_renaissance

# Generate an auto-Odyssey from C's influence graph
uv run atlas auto-odyssey "C"

# Rebuild the database after editing JSON source files
make build

# Regenerate Markdown documentation
make docs
```

## Makefile Targets

| Target | Description |
|---|---|
| `make init` | Set up virtualenv, install deps, build database |
| `make build` | Rebuild SQLite from JSON sources |
| `make server` | Start FastAPI dev server on port 8084 |
| `make audit` | Run AtlasAuditor |
| `make dark-matter` | Run missing-profile audit |
| `make test` | Run test suite |
| `make harden` | type-check + audit + test |
| `make type-check` | mypy |
| `make test-intensive` | Long-running analytical tests |
| `make docs` | Regenerate `generated-docs/` Markdown tree |
| `make site` | Export static HTML into `site/` |
| `make pages` | Prepare gh-pages artifacts (gh-pages branch only) |
| `make clean` | Remove generated artifacts |

## Setup and Run

1. `make init` — bootstrap virtualenv and build database
2. `make server` — start the server; open http://localhost:8084
3. `make docs` — regenerate Markdown docs
4. `atlas --help` — explore CLI commands

## GitHub Pages Deployment

A static export with a client-side SQLite database can be published to
GitHub Pages from the `gh-pages` branch. `make pages` rebuilds the
database, runs `SiteCrawler` to write `site/`, and copies the database
into `site/db/atlas/` for sql.js-httpvfs range-request access.

See [`GH_PAGES.md`](../GH_PAGES.md) for the full workflow.
