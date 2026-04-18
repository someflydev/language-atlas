# Atlas Toolkit

A suite of zero-dependency Python scripts and shell utilities for deep introspection, auditing, and maintenance of the Language Atlas data.

## Overview

The Atlas Toolkit provides essential utilities for maintaining the integrity of the programming language data lake (JSON) and its corresponding warehouse (SQLite). These tools use only the Python Standard Library and are designed to be run from the project root.

## Core Utilities

### atlas-fuzzy.sh

Fuzzy-search the entire Atlas and immediately jump to the TUI or detailed Info view.

- **Purpose:** Rapid navigation and discovery within the dataset.
- **Usage:** `./scripts/atlas-fuzzy.sh`
- **Key Features:**
  - Interactive selection via `fzf`.
  - Press **ENTER** to launch the interactive Terminal UI (TUI).
  - Press **CTRL-I** to view the static language profile (Info).

**Example Output:**
```text
Living Atlas > Python
> Python (1991)
  Ruby (1995)
  Perl (1987)
  ...
ENTER: TUI | CTRL-I: Info | ESC: Exit
```

### check_integrity.py

A deep-scanner for validating JSON field completeness and value constraints.

- **Purpose:** Surface missing data or inconsistent formatting in the core JSON before it is committed or ingested into the database.
- **Usage:** `uv run python scripts/check_integrity.py`
- **Validation Rules:**
  - Checks for missing or empty mandatory fields (e.g., `philosophy`, `key_innovations`).
  - Validates that the `year` is within reasonable historical bounds (1800-Present).

**Example Output:**
```text
=== Language Atlas: Integrity Check ===
Scanning 110 entries...

Found 2 integrity issues:
 - Jacquard Loom:
   * Year out of bounds: 1804 (Range: 1940-2026)
 - Mojo:
   * Empty field: influenced
```

### data_stats.py

Provides high-level metrics and distributions across the dataset.

- **Purpose:** Monitor dataset growth, balance across generations/clusters, and track Keystone Density.
- **Usage:** `uv run python scripts/data_stats.py`
- **Key Metrics:**
  - Total language count.
  - Keystone Density (percentage of languages marked as `is_keystone`).
  - Distribution by generation, cluster, and safety model.

**Example Output:**
```text
=== Language Atlas Statistics ===
Total Languages: 110
Keystone Languages: 73 (66.4% Keystone Density)

Distribution by Generation
Generation  | Count | %    
---------------------------
web1        | 36    | 32.7%
early       | 34    | 30.9%
...
```

### dark_matter_audit.py

The specialized "Dark Matter Audit" tool for identifying missing content profiles.

- **Purpose:** Scan the entire Atlas to identify every referenced language, concept, organization, and person that lacks a deep-dive JSON profile.
- **Usage:** `uv run python scripts/dark_matter_audit.py`
- **Output:** Generates `generated-reports/dark_matter_todo.json`, the authoritative TODO list for implementation phases.
- **Features:**
  - **Canonicalization:** Deduplicates variations in casing and punctuation.
  - **LLM-managed semantic alias layer:** Loads reviewed mappings from
    `data/.dark_matter_aliases.json` and
    `data/.dark_matter_canonicals.json`.
  - **Entity Detection:** Identifies missing profiles for organizations, historical events, and people.

Mechanical normalization such as punctuation cleanup, year stripping, and
event slugging stays in Python inside `scripts/dark_matter_audit.py`.
Semantic merges belong in the hidden JSON files:

- `data/.dark_matter_aliases.json`: human-readable alias term to reviewed
  canonical display term.
- `data/.dark_matter_canonicals.json`: canonical display term to declared
  type, plus optional `profile_key` for profile-stem matching.

When future prompt sessions decide two terms should be treated as the same
dark matter entry, extend these hidden JSON files instead of adding new
hardcoded semantic alias logic to the audit script.

**Example Output:**
```text
Audit complete. Results written to generated-reports/dark_matter_todo.json
Missing Languages: 82
Missing Entities: 1833
Missing Organizations: 20
Missing Events: 12
```

The output file `generated-reports/dark_matter_todo.json` is committed to the repository so the TODO list is visible in git history as the data corpus grows.

### audit_lineage.py

Validates the influence graph and identifies structural anomalies.

- **Purpose:** Ensure the integrity of the influence network and find isolated entries.
- **Usage:** `uv run python scripts/audit_lineage.py`
- **Checks:**
  - **Broken References:** Identifies names in influence fields that do not exist as primary entries.
  - **Isolated Islands:** Finds languages with zero incoming and zero outgoing influences.

**Example Output:**
```text
=== Language Atlas: Lineage Audit ===

Found 94 Broken References:
 - BASIC (influenced): Visual Basic (Not Found)
 - APL (influenced): Numpy (Not Found)
 ...
No isolated islands found.
```

## Generation & Reporting

### generate_reports.py

The "Atlas Analytics" suite for generating specialized, high-signal reports from the SQLite database.

- **Purpose:** Provide deep insights into the "Evolution of Programming" through modular reports.
- **Usage:** `uv run python scripts/generate_reports.py --report all`
- **Supported Reports:**
  - `safety_complexity`: Decade-over-decade trends in language safety.
  - `creator_impact`: Leaderboard of creators by influence score.
  - `cluster_genealogy`: Cross-pollination of ideas between language clusters.
  - `innovation_trends`: Dominant technological themes by era.
  - `db_health`: Identifies orphans and terminal languages.

**Example Output:**
```text
Generating db_health report...
Report saved to generated-reports/db_health.json
Done.
```

#### Report Artifacts

All outputs are written to `generated-reports/`. Re-run `uv run python scripts/generate_reports.py --report all` to regenerate.

**safety_complexity_trends.json** — Tracks the evolution of language safety and complexity over time. Key fields: `avg_complexity` (numerical mapping of complexity bias per decade) and `safety_distribution` (count of languages by safety model per decade). Use this to visualize whether languages are becoming safer or more complex across decades.

**creator_impact.json** — Ranks the architects of the Language Atlas by influence. Key fields: `total_impact` (sum of influence scores for all languages a creator is credited with) and `language_count`. Identifies the most influential individuals and organizations in programming history.

**cluster_genealogy.json** — Measures cross-pollination between language clusters. Key fields: `internal` (same-cluster influences), `external` (cross-cluster influences), and `ratio`. High internal ratios indicate self-referential ecosystems (e.g., Systems); high external ratios indicate broad foundational impact (e.g., Mathematics).

**innovation_trends.json** — Captures dominant technological themes by era. Groups key innovations from language profiles by generation (dawn, early, web1, renaissance). Functions as a keyword cloud of the core advancements that defined each stage of programming evolution.

**db_health.json** — Identifies structural anomalies and missing content. Checks: `orphans` (languages with no influences), `terminal` (influenced-but-never-influenced-others), and `high_influence_missing_profiles` (high-impact languages lacking a profile). A maintenance tool for gap analysis in the lineage graph.

### export_summary.py

Generates tabular summaries of the dataset for external reporting or spreadsheets.

- **Purpose:** Create portable summaries in CSV or Markdown formats.
- **Usage:** `uv run python scripts/export_summary.py --format md --output summary.md`
- **Supported Formats:** CSV (default) and Markdown (`md`).

**Example Output:**
```text
Name,Year,Creators,Generation,Cluster,Keystone
Jacquard Loom,1804,Joseph Marie Jacquard,dawn,historical,Yes
Analytical Engine,1837,"Charles Babbage, Ada Lovelace",dawn,historical,Yes
...
```

## Database Utilities

### db_query.py

A lightweight CLI wrapper for ad-hoc SQL queries against the Language Atlas SQLite database.

- **Purpose:** Query the "warehouse" directly without requiring the `sqlite3` binary installed on the system.
- **Usage:** `uv run python scripts/db_query.py "SELECT name, year FROM languages WHERE is_keystone = 1 LIMIT 3"`

**Example Output:**
```text
Connected to: language_atlas.sqlite

name              | year
------------------------
Jacquard Loom     | 1804
Analytical Engine | 1837
Boolean Algebra   | 1847

(3 rows returned)
```

### inspect_sqlite.py

Provides a deep inspection of the SQLite schema and data samples for all tables.

- **Purpose:** Debugging the database schema and verifying the results of the data pipeline.
- **Usage:** `uv run python scripts/inspect_sqlite.py`

**Example Output:**
```text
Found 49 tables in language_atlas.sqlite

================================================================================
TABLE: languages (110 rows)
--------------------------------------------------------------------------------
Columns: id, name, year, cluster, generation, is_keystone ...
Sample Data:
  Row 1: { "id": 1, "name": "Jacquard Loom", "year": 1804 ... }
```

## Distribution

### build_zenith.py

Builds a standalone, zero-dependency binary of the Language Atlas CLI and TUI.

- **Purpose:** Package the application for distribution to environments without Python or dependencies.
- **Usage:** `uv run python scripts/build_zenith.py`
- **Features:**
  - Bundles the SQLite database and all data files.
  - Generates a single-file executable using PyInstaller.

**Example Output:**
```text
[*] Starting Zenith Build...
[*] Running PyInstaller...
INFO: PyInstaller: 6.x.x
...
[*] Zenith Build Complete: dist/atlas
```

## Maintenance

These scripts should be run as part of the data ingestion or modification workflow to ensure no regressions are introduced to the influence graph or data schemas.
