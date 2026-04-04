# Atlas Control Center: Codebase and Semantic Schema

Welcome to the internal engine of the Language Atlas. This guide covers the technical architecture, the Semantic Schema powering our SQLite views, and the core logic that connects our data to the interactive dashboards.

## Architecture Overview

The codebase is split into three primary layers:

1.  **Core Logic (`src/app/core/`)**:
    *   `data_loader.py`: The unified data access layer. It handles transparent switching between flat JSON files and the SQLite backend. It hydrates complex language objects, including creator and paradigm relations.
    *   `build_sqlite.py`: The database orchestrator. It transforms the raw JSON lake into a structured relational database with full-text search (FTS5) capabilities.
    *   `insights.py`: Analytical engine for generating cross-language historical reports.
2.  **CLI Interface (`src/cli.py`)**:
    *   A high-density Control Room built with Typer and Rich.
    *   Features a `dashboard` command for real-time visual analysis of language impact.
    *   Includes fuzzy name suggestion logic to help discover languages with complex naming.
3.  **Interactive TUI (`src/tui.py`)**:
    *   The Living Atlas TUI provides an immersive, three-pane experience for exploring language evolution.
    *   Features real-time FTS5 global search and deep navigation through influence scores.
4.  **Web Application (`src/app/`)**:
    *   FastAPI-powered server providing an interactive, filtered view of the programming language timeline.

## The Semantic Schema (SQLite Views)

Our database uses Semantic Views to abstract away complex JOINs and provide a clean API for both the CLI and Web layers.

### `v_language_details`
Provides a flattened, comprehensive view of a language's metadata.
*   **Columns**: `id`, `name`, `display_name`, `year`, `cluster`, `generation`, `profile_title`, `paradigms` (comma-separated), `creators` (comma-separated).
*   **Usage**: Powering the `dashboard` and `info` commands.

### `v_global_search`
A unified interface for full-text search across both core metadata and deep technical profiles.
*   **Columns**: `category`, `language_id`, `title`, `snippet`, `source_table`.
*   **Logic**: Unions `fts_languages` and `fts_profiles` to provide a Google-style search experience.

### Full-Text Search (FTS5)
We leverage SQLite's `fts5` module for high-performance discovery:
*   `fts_languages`: Optimized for searching names, philosophies, and mental models.
*   `fts_profiles`: Optimized for deep-diving into the narrative sections of language documentation.

## CLI: Control Room Commands

The CLI is the primary tool for data-dense research.

```bash
# Launch the interactive Living Atlas TUI
uv run python3 src/cli.py tui

# Enter the Control Room for a specific language
uv run python3 src/cli.py dashboard "Rust"

# Generate a visual summary of release density
uv run python3 src/cli.py report summary

# Get a syntax-highlighted technical brief
uv run python3 src/cli.py info "C++" --pretty

# Perform a global semantic search
uv run python3 src/cli.py search "memory safety"
```

## Fuzzy Discovery Tools

In addition to the standard CLI, we provide a zero-config fuzzy finder for rapid exploration.

```bash
# Launch the fuzzy-search wrapper (requires fzf)
# Use ENTER for TUI or CTRL-I for a quick Info brief
bash scripts/atlas-fuzzy.sh
```

## Internal Core Logic

### The DataLoader Lifecycle
1.  **Initialization**: Checks for `USE_SQLITE=1` environment variable.
2.  **Discovery**: Scans `data/docs/language_profiles/` for extended technical specs.
3.  **Hydration**: When fetching a language, it automatically joins related creators, paradigms, and influences into a single Python dictionary.

### Fuzzy Suggestion Engine
The CLI uses `difflib.get_close_matches` against the database's name index. This ensures that even if you misspell a language, the Atlas provides an intelligent redirection.

## Makefile Commands

The project includes a Makefile to automate common development tasks.

*   `make docs`: Generates Markdown documentation files in the `generated-docs/` directory by querying the SQLite database.
*   `make test`: Executes the fast test suite, covering unit tests and data consistency checks while excluding intensive analytical tests.
*   `make test-intensive`: Runs the full test suite, including long-running analytical tests, and regenerates the `historical_insights.json` report.
*   `make clean`: Removes all generated artifacts, including the `generated-docs/` directory, pytest caches, and the historical insights report.
*   `make help`: Displays a summary of all available make targets and their descriptions.

## Setup and Run

### 1. Install Dependencies
```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

### 2. Build the Database
```bash
uv run python3 src/app/core/build_sqlite.py
```

### 3. Start the Web UI
```bash
uv run python3 src/app/app.py
```

### 4. Run CLI Commands
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
uv run python3 src/cli.py --help
```
