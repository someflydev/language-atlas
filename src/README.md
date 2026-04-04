# 🏛️ Atlas Control Center: Codebase & Semantic Schema

Welcome to the internal engine of the Language Atlas. This guide covers the technical architecture, the "Semantic Schema" powering our SQLite views, and the core logic that connects our data to the interactive dashboards.

## 🏗️ Architecture Overview

The codebase is split into three primary layers:

1.  **Core Logic (`src/app/core/`)**:
    *   `data_loader.py`: The unified data access layer. It handles transparent switching between flat JSON files and the SQLite backend. It hydrates complex language objects, including creator and paradigm relations.
    *   `build_sqlite.py`: The database orchestrator. It transforms the raw JSON "lake" into a structured relational database with full-text search (FTS5) capabilities.
    *   `insights.py`: Analytical engine for generating cross-language historical reports.
2.  **CLI Interface (`src/cli.py`)**:
    *   A high-density "Control Room" built with `Typer` and `Rich`.
    *   Features a `dashboard` command for real-time visual analysis of language impact.
    *   Includes fuzzy name suggestion logic to help discover languages with complex naming (e.g., `ALGOL_60`).
3.  **Web Application (`src/app/`)**:
    *   FastAPI-powered server providing an interactive, filtered view of the programming language timeline.

## 🔍 The Semantic Schema (SQLite Views)

Our database uses **Semantic Views** to abstract away complex JOINs and provide a clean API for both the CLI and Web layers.

### `v_language_details`
Provides a flattened, comprehensive view of a language's metadata.
*   **Columns**: `id`, `name`, `display_name`, `year`, `cluster`, `generation`, `profile_title`, `paradigms` (comma-separated), `creators` (comma-separated).
*   **Usage**: Powering the `dashboard` and `info` commands.

### `v_global_search`
A unified interface for full-text search across both core metadata and deep technical profiles.
*   **Columns**: `category`, `language_id`, `title`, `snippet`, `source_table`.
*   **Logic**: Unions `fts_languages` and `fts_profiles` to provide a "Google-style" search experience.

### Full-Text Search (FTS5)
We leverage SQLite's `fts5` module for high-performance discovery:
*   `fts_languages`: Optimized for searching names, philosophies, and mental models.
*   `fts_profiles`: Optimized for deep-diving into the narrative sections of language documentation.

## 🛠️ CLI: Control Room Commands

The CLI is the primary tool for data-dense research.

```bash
# Enter the Control Room for a specific language
python3 src/cli.py dashboard "Rust"

# Generate a visual summary of release density
python3 src/cli.py report summary

# Get a syntax-highlighted technical brief
python3 src/cli.py info "C++" --pretty

# Perform a global semantic search
python3 src/cli.py search "memory safety"
```

## 🧠 Internal Core Logic

### The `DataLoader` Lifecycle
1.  **Initialization**: Checks for `USE_SQLITE=1` environment variable.
2.  **Discovery**: Scans `data/docs/language_profiles/` for extended technical specs.
3.  **Hydration**: When fetching a language, it automatically joins related creators, paradigms, and influences into a single Python dictionary.

### Fuzzy Suggestion Engine
The CLI uses `difflib.get_close_matches` against the database's name index. This ensures that even if you misspell a language (e.g., `info rustt`), the Atlas provides an intelligent redirection.

## 🚀 Setup & Run

### 1. Install Dependencies
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r src/app/requirements.txt
uv add typer rich
```

### 2. Build the Database (Optional but Recommended)
```bash
python3 src/app/core/build_sqlite.py
```

### 3. Start the Web UI
```bash
python3 src/app/app.py
```

### 4. Run CLI Commands
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 src/cli.py --help
```
