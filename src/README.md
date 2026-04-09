# Atlas Control Center: Zenith Platform & Semantic Schema

Welcome to the **Zenith** state of the Language Atlas—a professional-grade research platform for exploring the evolution of programming languages through guided mastery and semantic discovery.

## Architecture Overview

The Language Atlas is a data-driven platform where JSON is the single source of truth, integrated across four primary layers:

1.  **Core Logic & Audit (src/app/core/)**:
    *   `data_loader.py`: Unified data access layer with transparent SQLite/JSON switching.
    *   `auditor.py`: **Atlas Auditor (Validation 2.0)**. Provides JSON schema validation and referential integrity checks.
    *   `build_sqlite.py`: Transforms the JSON data lake into a structured, indexed relational database.
    *   `site_builder.py`: **Site Builder**. Contains two output modes:
        *   `SiteBuilder` generates the `generated-docs/` Markdown tree (language profiles, concept profiles, era summaries, thematic documents, homepage INDEX.md, and project README.md) by calling DataLoader methods. `scripts/generate_docs.py` is a thin CLI wrapper around it.
        *   `SiteCrawler` (HTML export) spins up the real FastAPI app via `fastapi.testclient.TestClient` and walks every exported GET route. Each response is written to `site/<path>/index.html`. After fetching, `_rewrite_links` converts absolute internal URLs into relative paths correct for the file's depth in the tree. Static assets under `src/app/static/` are mirrored verbatim into `site/static/`. HTMX-driven pages are exported in their fully-rendered, unfiltered server state; the filter form is preserved but an `ATLAS_STATIC_MODE` notice is injected near the top of each page. Run via `make site`.
2.  **The Pedagogical Engine: Interactive Odysseys**:
    *   **Guided Paths**: Curated learning paths (e.g., "The Systems Renaissance") that pull narrative challenges directly from language profiles.
    *   **Auto-Odyssey**: A dynamic, recursive engine that generates lineage-based learning paths on the fly using SQLite Recursive CTEs to find influential descendants.
3.  **Discovery Interfaces**:
    *   **CLI (src/cli.py)**: High-density "Control Room" for analytical reports, guided Odysseys, and the new `auto-odyssey` command.
    *   **Living Atlas TUI (src/tui.py)**: Immersive three-pane explorer with real-time FTS5 search and narrative Odyssey mode (toggle with `o`).
    *   **Web UI & API (src/app/app.py)**: FastAPI server providing a rich visual timeline, interactive Odysseys, and a comprehensive **Semantic Search API**.
    *   **Data Visualizations (Plotly + Polars)**: Interactive, high-fidelity visualizations of the Atlas timeline and influence network, powered by **Polars** for high-performance data processing.
4.  **Distribution (Zenith Build)**:
    *   A self-contained executable binary that bundles the entire platform, including the database and dependencies.

## Semantic Search & Visualization API

The Atlas exposes a high-performance JSON and Visualization API for external tools and programmatic research. The base URL `/api` provides interactive documentation.

*   **API Base**: `GET /api` (Living documentation of all endpoints)
*   **Search**: `GET /api/search?q=concurrency` (FTS5 BM25 ranked across languages, profiles, and concepts)
*   **Visualizations**: `GET /visualizations` (Interactive Plotly dashboard)
*   **Viz Data**: `GET /api/viz/timeline` and `GET /api/viz/influence` (Raw data for visualization layers)
*   **Odysseys**: `GET /api/odysseys` (List all guided paths)
*   **Language Profiles**: `GET /api/language/Rust` (Combined core + deep profile data)

## Data Architecture & Performance

The platform utilizes a hybrid data processing strategy:
- **Primary Engine**: **Polars** is used for high-performance backend data transformation, sorting, and analytical calculations.
- **Relational Layer**: **SQLite (FTS5)** provides indexed full-text search and complex relational queries.
- **Visualization Layer**: **Plotly Express** handles rendering, utilizing a **Pandas/PyArrow** compatibility bridge for seamless data handover between Polars and the UI.

## Atlas Auditor: Validation 2.0

The `AtlasAuditor` class and the `scripts/dark_matter_audit.py` tool provide a rigorous quality gate:

```bash
# Run the auditor and integrity checks
make audit

# Identify "Dark Matter" (missing profiles referenced in the data)
uv run python3 scripts/dark_matter_audit.py
```

## Control Room & Server Commands

```bash
# Start a Guided Odyssey in the CLI
uv run atlas odyssey systems_renaissance

# Generate a Dynamic Odyssey based on influence
uv run atlas auto-odyssey "C"

# Launch the FastAPI Web Server & API
make server

# Regenerate all Markdown documentation from JSON/SQLite sources
make docs
```

## Makefile Targets

*   **server**: Starts the FastAPI web server on `http://localhost:8084`.
*   **docs**: Regenerates all Markdown documentation in `generated-docs/` (Languages, Eras, Concepts, and Thematic Overviews) from the SQLite database.
*   **audit**: Runs the Atlas Auditor and consistency checks.
*   **test**: Runs fast unit and consistency checks.
*   **build**: Builds the standalone Zenith binary.
*   **clean**: Removes generated artifacts and temporary files.

## Setup and Run

1.  **Install Dependencies**: `uv sync`
2.  **Build Database**: `uv run python3 src/app/core/build_sqlite.py`
3.  **Regenerate Docs**: `make docs`
4.  **Explore**: Use `atlas --help` or visit `http://localhost:8084/api`.

## GitHub Pages Deployment

A static export with a client-side SQLite database can be published to
GitHub Pages from the `gh-pages` branch. The export is produced by
`make pages`, which rebuilds the database, runs `SiteCrawler` to write
`site/`, and copies the database into `site/db/atlas/` for
`sql.js-httpvfs` HTTP range-request access.

See [`docs/GH_PAGES.md`](../docs/GH_PAGES.md) for the full build and
deploy workflow, local preview instructions, and troubleshooting.
