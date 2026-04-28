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
  SQL except DataLoader and InsightGenerator. Paradigm browsing now has
  a first-class `get_paradigm_ecosystem()` contract that returns the
  paradigm record, language-only members, foundation-only upstream
  context, and summary stats without changing the lightweight paradigm
  detail endpoint. Language-like profile loading now also keeps upstream
  influence entity types attached so the shared profile template can
  distinguish foundational precursors from direct language ancestors
  without breaking the older flat influence lists.
- **`build_sqlite.py`** — Transforms the JSON source files into
  `language_atlas.sqlite`. Calculates `influence_score`, builds the
  FTS5 `search_index` virtual table, creates analytical views, and
  populates materialized influence closure tables. Run via `make build`.
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

## Generated and Legacy Artifacts

### `generated-data/`

Derived JSON artifacts produced by `make derived-data`
(`scripts/generate_derived_data.py`). Gitignored; rebuilt on demand.
Read by Phase 3 API endpoints.

### Web server (`src/app/app.py`)

FastAPI application serving all HTML and JSON routes on port 8084.
See `API_GUIDE.md` for the full endpoint reference and `.context/routes.md`
for the complete route-to-template map. The core `/language/{name}`
profile route is shared by the mixed `languages` corpus, so
`entity_type="foundation"` and `entity_type="artifact"` records render
through the same template without being relabeled as executable
languages. That shared profile view now renders grouped upstream
influences for language-like entities, separating conceptual
foundations from direct language lineage. It also injects closure-table
lineage data into profile pages so they can show transitive ancestry,
notable descendants, and graph role indicators without running recursive
queries during request handling.

### CLI (`src/cli.py`)

Typer CLI exposing terminal-native views over the same mixed
language/foundation/artifact corpus as the web app. Notable commands:

- `atlas paradigm <name>` for the foundation-aware paradigm ecosystem
- `atlas influences <name>` for grouped upstream lineage plus downstream impact
- `atlas dashboard <name>` for the control-room view with typed lineage groups
- `atlas odyssey <id>` and `atlas auto-odyssey <language>` for guided paths

Run with `uv run atlas --help`.

### TUI (`src/tui.py`)

Textual three-pane browser with real-time search across language-like
entities and an Odyssey mode (toggle with `o`). The chronology pane now
defaults to languages, and `m` cycles browse mode through languages,
foundations, artifacts, and the mixed corpus so non-language precursors
are explicitly discoverable instead of silently omitted. The reader and
nexus panes both use grouped lineage labels, separating foundational
precursors from direct language ancestors. Run with `uv run atlas tui`.

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
- `GET /api/paradigm/Functional/ecosystem` — paradigm languages plus ranked foundations
- `GET /api/odysseys` — list all guided paths
- `GET /visualizations` — Plotly timeline and influence network

For `/api/language/{name}`, compatibility fields like `influenced_by`
remain flat lists, while richer consumers can use
`influenced_by_details` and `upstream_influence_groups` to distinguish
foundations, language ancestors, and related artifacts.

## Data Architecture

- **Polars** handles backend data transformation, sorting, and
  aggregation before results are passed to routes.
- **SQLite (FTS5)** provides indexed full-text search and the
  relational query layer for all analytical features.
- **Plotly Express** renders visualizations, using a Pandas/PyArrow
  bridge to consume Polars DataFrames.

## Data Flow

Build time:

```text
JSON + data/docs/
    -> build_sqlite.py
    -> tables and views
    -> materialized influence closure tables
    -> language_atlas.sqlite
```

The closure population phase runs after table and view creation. It
materializes ancestry, descendants, reachability, and bounded lineage
paths so runtime lineage queries do not need to evaluate recursive CTEs
on each request.

Optional post-build derived data:

```text
language_atlas.sqlite
    -> scripts/generate_derived_data.py
    -> generated-data/
```

## Language Schema Notes

The `languages` table in `language_atlas.sqlite` includes the following
core classification fields that drive browse behavior:

| Column | Meaning |
|---|---|
| `name` | Canonical Atlas identifier used in influence edges and routes |
| `display_name` | User-facing name for rendering, such as `F#` |
| `year` | First public appearance or introduction year |
| `cluster` | Functional ecosystem grouping such as `systems`, `frontend`, or `academic` |
| `generation` | Broad era bucket such as `early`, `web1`, or `renaissance` |
| `entity_type` | Atlas classification: `language`, `foundation`, or `artifact` |

`entity_type` semantics:
- `language`: executable programming languages and language families used in normal language-browse views
- `foundation`: theoretical, historical, and conceptual precursors such as Turing Machine or BNF
- `artifact`: runtimes, tools, libraries, formats, and UI/runtime systems such as JVM, React, or JSON

`DataLoader.get_all_languages()` now defaults to `entity_type="language"`.
Callers that need the full mixed corpus must pass `entity_type=None` or an
explicit non-language type.

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

# Inspect a paradigm ecosystem with ranked foundations
uv run atlas paradigm Functional

# See grouped lineage for a language-like entity
uv run atlas influences Scala

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
| `make derived-data` | Generate derived JSON artifacts in `generated-data/` |
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
