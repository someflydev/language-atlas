# Atlas Control Center: Zenith Platform & Semantic Schema

Welcome to the **Zenith** state of the Language Atlas—a professional-grade research platform for exploring the evolution of programming languages through guided mastery and semantic discovery.

## Architecture Overview

The Language Atlas is now a fully integrated platform with four primary layers:

1.  **Core Logic & Audit (`src/app/core/`)**:
    *   `data_loader.py`: Unified data access layer with transparent SQLite/JSON switching.
    *   `auditor.py`: **Atlas Auditor (Validation 2.0)**. A robust class providing JSON schema validation, referential integrity checks, and "Semantic Orphan" detection.
    *   `build_sqlite.py`: Transforms the JSON data lake into a structured, indexed relational database.
2.  **Guided Mastery: Interactive Odysseys**:
    *   Implemented across CLI, TUI, and Web.
    *   Curated learning paths (e.g., "The Systems Renaissance") guide users through language milestones with technical challenges.
3.  **Discovery Interfaces**:
    *   **CLI (`src/cli.py`)**: High-density "Control Room" for analytical reports and guided Odysseys.
    *   **Living Atlas TUI (`src/tui.py`)**: Immersive three-pane explorer with real-time FTS5 search and Odyssey mode (toggle with `o`).
    *   **Web UI & API (`src/app/app.py`)**: FastAPI server providing a rich visual timeline, interactive Odysseys, and a **Semantic Search API**.
4.  **Distribution (Zenith Build)**:
    *   A self-contained executable binary that bundles the entire platform, including the database and dependencies.

## Semantic Search API

The Atlas exposes a high-performance JSON API for external tools and programmatic research.

-   **Search**: `GET /api/search?q=concurrency` (FTS5 BM25 ranked)
-   **Odysseys**: `GET /api/odysseys` (List all paths)
-   **Language Profiles**: `GET /api/language/Rust` (Combined core + deep profile)

Refer to `docs/api.md` for full documentation and integration examples.

## Atlas Auditor: Validation 2.0

The `AtlasAuditor` class provides a rigorous quality gate for our data graph:

```python
from app.core.auditor import AtlasAuditor
auditor = AtlasAuditor()
success, errors, warnings = auditor.run_all()
# Detects "Semantic Orphans" (languages without influences or paradigms)
```

## Control Room & TUI Usage

```bash
# Start a Guided Odyssey in the CLI
uv run atlas odyssey systems_renaissance

# Toggle Odyssey Mode in the TUI
uv run atlas tui  # Then press 'o'

# Launch the FastAPI Web Server & API
uv run python3 src/app/app.py
```

## Distribution & Portability

The Atlas can be packaged as a single-file standalone binary:

```bash
# Build the Zenith distribution
uv run python3 scripts/build_zenith.py

# Run the portable binary (no local dependencies required)
./dist/atlas dashboard "Lisp"
```

## Makefile Commands

*   `make docs`: Generates Markdown documentation from the SQLite database.
*   `make test`: Runs fast unit and consistency checks (includes Atlas Auditor).
*   `make build`: Builds the standalone Zenith binary.
*   `make clean`: Removes generated artifacts and build temporary files.

## Setup and Run

1.  **Install Dependencies**: `uv sync`
2.  **Build Database**: `uv run python3 src/app/core/build_sqlite.py`
3.  **Audit Data**: `uv run pytest tests/test_auditor.py`
4.  **Explore**: Use `atlas --help` or visit `http://localhost:8084`.
