# Atlas Toolkit

A suite of zero-dependency Python scripts for deep introspection, auditing, and maintenance of the Language Atlas data.

## Overview

The Atlas Toolkit provides essential utilities for maintaining the integrity of the programming language data lake (JSON) and its corresponding warehouse (SQLite). These tools use only the Python Standard Library and are designed to be run from the project root.

## Tools

### data_stats.py

Provides high-level metrics and distributions across the dataset.

- **Purpose:** Monitor dataset growth, balance across generations/clusters, and track Keystone Density.
- **Usage:** `uv run scripts/data_stats.py`
- **Key Metrics:**
  - Total language count.
  - Keystone Density (percentage of languages marked as `is_keystone`).
  - Distribution by generation, cluster, and safety model.

**Example Output:**
```text
=== Language Atlas Statistics ===
Total Languages: 95
Keystone Languages: 65 (68.4% Keystone Density)

Distribution by Generation
Generation  | Count | %    
---------------------------
web1        | 30    | 31.6%
early       | 29    | 30.5%
...
```

### audit_lineage.py

Validates the influence graph and identifies structural anomalies.

- **Purpose:** Ensure the integrity of the influence network and find isolated entries.
- **Usage:** `uv run scripts/audit_lineage.py`
- **Checks:**
  - **Broken References:** Identifies names in `influenced_by` or `influenced` fields that do not exist as primary entries.
  - **Isolated Islands:** Finds languages with zero incoming and zero outgoing influences.

### check_integrity.py

A deep-scanner for validating JSON field completeness and value constraints.

- **Purpose:** Surface missing data or inconsistent formatting in the core JSON.
- **Usage:** `uv run scripts/check_integrity.py`
- **Validation Rules:**
  - Checks for missing or empty mandatory fields (e.g., `philosophy`, `key_innovations`).
  - Validates that the `year` is within reasonable historical bounds (Default: 1800-Present).

### export_summary.py

Generates tabular summaries of the dataset for external reporting.

- **Purpose:** Create portable summaries in CSV or Markdown formats.
- **Usage:** `uv run scripts/export_summary.py --format md --output summary.md`
- **Supported Formats:** CSV (default) and Markdown (`md`).

### db_query.py

A lightweight CLI wrapper for ad-hoc SQL queries against the Language Atlas SQLite database.

- **Purpose:** Query the "warehouse" directly without requiring the `sqlite3` binary.
- **Usage:** `uv run scripts/db_query.py "SELECT name, year FROM languages WHERE is_keystone = 1 LIMIT 5"`
- **Features:** Auto-locates the database in the project root or `data/` directory.

## Maintenance

These scripts should be run as part of the data ingestion or modification workflow to ensure no regressions are introduced to the influence graph or data schemas.
