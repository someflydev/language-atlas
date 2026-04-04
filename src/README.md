# Atlas Control Center: Codebase and Semantic Schema

Welcome to the internal engine of the Language Atlas. This guide covers the technical architecture, the Semantic Schema powering our SQLite views, and the core logic that connects our data to the interactive dashboards.

## Architecture Overview

The codebase is split into three primary layers:

1.  **Core Logic (`src/app/core/`)**:
    *   `data_loader.py`: The unified data access layer. Handles transparent switching between JSON files and SQLite.
    *   `build_sqlite.py`: The database orchestrator. Transforms the JSON "lake" into a structured relational database.
    *   `insights.py`: Analytical engine for generating cross-language historical reports.
2.  **CLI Interface (`src/cli.py`)**:
    *   A high-density Control Room built with Typer and Rich.
    *   Features a `dashboard` command for real-time visual analysis.
3.  **Interactive TUI (`src/tui.py`)**:
    *   The "Living Atlas" TUI provides an immersive, three-pane experience for exploring language evolution.
    *   Features real-time FTS5 global search and deep navigation through influence scores.
4.  **Web Application (`src/app/`)**:
    *   FastAPI-powered server providing a filtered view of the programming language timeline.

## SQLite: The Analytical Engine

The Language Atlas uses SQLite not just as a storage layer, but as a powerful analytical engine. We leverage advanced features to model complex historical relationships.

### Inspection Fundamentals

You can inspect the database state at any time:

```bash
# Basic inspection using our internal script
uv run python3 scripts/inspect_sqlite.py

# Direct CLI access
sqlite3 language_atlas.sqlite
```

### Feature Progression: From Basic to Complex

We leverage SQLite's capabilities in increasing order of sophistication:

1.  **Basic Relational (Foreign Keys & Indexes)**: Ensures data integrity across languages, paradigms, and creators.
2.  **Aggregated Views**: `v_language_details` provides flattened metadata for easy consumption by the UI.
3.  **Full-Text Search (FTS5)**: High-performance discovery across philosophies and technical profiles using the Porter stemming algorithm.
4.  **Reactive Triggers**: Automatic FTS index updates when core language data changes.
5.  **Window Functions**: Used in `insights.py` to calculate "Paradigm Volatility" (ranking decades by innovation density).
6.  **Recursive CTEs**: Powerful graph traversals to calculate the "transitive influence" of keystone languages like ALGOL 60 or Lisp.

### Core Schema Highlights

The most interesting data resides in these tables:

*   **`languages`**: Core metadata including `influence_score`, `year`, and `generation`.
*   **`influences`**: A many-to-many relationship mapping the "lineage" of code.
*   **`language_profiles`**: Extended technical narratives split into `profile_sections`.
*   **`era_summaries`**: Contextual data about specific historical periods (e.g., "Web Explosion").

### Query Progression: Understanding the Logic

The system performs queries of varying difficulty behind the scenes:

*   **Level 1: Simple Filter (Basic)**
    ```sql
    SELECT name FROM languages WHERE cluster = 'systems';
    ```
*   **Level 2: Complex Join (Intermediate)**
    ```sql
    SELECT p.name FROM paradigms p 
    JOIN language_paradigms lp ON p.id = lp.paradigm_id 
    WHERE lp.language_id = ?;
    ```
*   **Level 3: Full-Text Search (Advanced)**
    ```sql
    SELECT title, snippet(fts_languages, -1, '[b]', '[/b]', '...', 10) 
    FROM fts_languages WHERE fts_languages MATCH 'memory safety';
    ```
*   **Level 4: Recursive Graph Traversal (Clever)**
    ```sql
    WITH RECURSIVE influence_chain(id, name, depth) AS (
        SELECT id, name, 0 FROM languages WHERE name = 'C'
        UNION ALL
        SELECT l.id, l.name, ic.depth + 1
        FROM languages l JOIN influences i ON l.id = i.target_id
        JOIN influence_chain ic ON i.source_id = ic.id
    ) SELECT name, MIN(depth) FROM influence_chain GROUP BY name;
    ```

## CLI: Control Room Commands

```bash
# Launch the interactive Living Atlas TUI
uv run python3 src/cli.py tui

# Enter the Control Room for a specific language
uv run python3 src/cli.py dashboard "Rust"

# Perform a global semantic search
uv run python3 src/cli.py search "memory safety"
```

## Makefile Commands

*   `make docs`: Generates Markdown documentation from the SQLite database.
*   `make test`: Runs fast unit and consistency checks.
*   `make test-intensive`: Executes long-running analytical tests and regenerates insights.
*   `make clean`: Removes generated documentation and test artifacts.

## Setup and Run

1.  **Install Dependencies**: `uv venv --python 3.12 && source .venv/bin/activate && uv sync`
2.  **Build Database**: `uv run python3 src/app/core/build_sqlite.py`
3.  **Start Web UI**: `uv run python3 src/app/app.py`
4.  **Explore CLI**: `uv run python3 src/cli.py --help`
