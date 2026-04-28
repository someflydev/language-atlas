#!/usr/bin/env python3
import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "language_atlas.sqlite"
DEFAULT_OUT_DIR = REPO_ROOT / "generated-data"


def generated_at() -> str:
    return datetime.utcnow().isoformat() + "Z"


def row_to_language(row: sqlite3.Row) -> dict[str, Any]:
    display_name = row["display_name"] or row["name"]
    return {
        "name": row["name"],
        "display_name": display_name,
        "entity_type": row["entity_type"],
        "year": row["year"],
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        display_path = path.relative_to(Path.cwd())
    except ValueError:
        display_path = path
    print(f"Writing {display_path}")
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def build_lineage_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT
            l.id,
            l.name,
            l.display_name,
            l.entity_type,
            l.year,
            COUNT(DISTINCT la.ancestor_language_id) AS ancestor_count,
            COUNT(DISTINCT ld.descendant_language_id) AS descendant_count,
            COALESCE(MAX(la.depth), 0) AS max_ancestor_depth,
            COALESCE(MAX(ld.depth), 0) AS max_descendant_depth,
            (
                SELECT COUNT(*)
                FROM language_descendants ld_reachable
                WHERE ld_reachable.root_language_id = l.id
            ) AS reachability_score,
            (
                SELECT COUNT(*)
                FROM language_descendants ld_by
                WHERE ld_by.descendant_language_id = l.id
            ) AS reachable_by_score
        FROM languages l
        LEFT JOIN language_ancestry la ON la.root_language_id = l.id
        LEFT JOIN language_descendants ld ON ld.root_language_id = l.id
        GROUP BY l.id
        ORDER BY reachability_score DESC, l.name ASC
        """
    ).fetchall()

    languages = []
    for row in rows:
        item = row_to_language(row)
        item.update(
            {
                "ancestor_count": row["ancestor_count"],
                "descendant_count": row["descendant_count"],
                "max_ancestor_depth": row["max_ancestor_depth"],
                "max_descendant_depth": row["max_descendant_depth"],
                "reachability_score": row["reachability_score"],
                "reachable_by_score": row["reachable_by_score"],
            }
        )
        languages.append(item)

    return {
        "generated_at": generated_at(),
        "language_count": len(languages),
        "languages": languages,
    }


def lineage_scores(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {language["name"]: language for language in summary["languages"]}


def build_keystone_entities(
    conn: sqlite3.Connection, summary: dict[str, Any]
) -> dict[str, Any]:
    flagged = {
        row["name"]
        for row in conn.execute("SELECT name FROM languages WHERE is_keystone = 1").fetchall()
    }
    scored = []
    for language in summary["languages"]:
        keystone_score = (
            language["reachability_score"] * language["reachable_by_score"]
        )
        item = {
            "name": language["name"],
            "display_name": language["display_name"],
            "entity_type": language["entity_type"],
            "year": language["year"],
            "is_keystone_flag": language["name"] in flagged,
            "reachability_score": language["reachability_score"],
            "reachable_by_score": language["reachable_by_score"],
            "keystone_score": keystone_score,
        }
        scored.append(item)

    selected: dict[str, dict[str, Any]] = {}
    for item in sorted(
        scored,
        key=lambda value: (-value["keystone_score"], value["name"]),
    )[:30]:
        selected[item["name"]] = item

    for item in scored:
        if item["is_keystone_flag"]:
            selected[item["name"]] = item

    keystones = sorted(
        selected.values(),
        key=lambda value: (-value["keystone_score"], value["name"]),
    )
    return {
        "generated_at": generated_at(),
        "count": len(keystones),
        "keystones": keystones,
    }


def build_bridge_entities(conn: sqlite3.Connection) -> dict[str, Any]:
    language_rows = conn.execute(
        """
        SELECT name, display_name, entity_type, year
        FROM languages
        ORDER BY name
        """
    ).fetchall()
    language_by_name = {row["name"]: row for row in language_rows}
    paths = conn.execute(
        """
        SELECT DISTINCT path_text
        FROM language_lineage_paths_bounded
        WHERE depth >= 2
        """
    ).fetchall()

    path_texts_by_middle: dict[str, set[str]] = {
        name: set() for name in language_by_name
    }
    for row in paths:
        path_text = row["path_text"]
        parts = path_text.split(" -> ")
        for middle_name in set(parts[1:-1]):
            if middle_name in path_texts_by_middle:
                path_texts_by_middle[middle_name].add(path_text)

    bridge_counts = {
        name: len(path_texts)
        for name, path_texts in path_texts_by_middle.items()
        if path_texts
    }
    threshold = 2
    if 0 < len([count for count in bridge_counts.values() if count >= threshold]) < 10:
        threshold = 1
        print(
            "Warning: fewer than 10 bridge candidates found; "
            "including bridge_count >= 1",
            file=sys.stderr,
        )

    bridges = []
    for name, count in bridge_counts.items():
        if count < threshold:
            continue
        row = language_by_name[name]
        item = row_to_language(row)
        item["bridge_count"] = count
        bridges.append(item)

    bridges.sort(key=lambda value: (-value["bridge_count"], value["name"]))
    bridges = bridges[:50]
    return {
        "generated_at": generated_at(),
        "count": len(bridges),
        "bridges": bridges,
    }


def build_orphan_subgraphs(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT l.name, l.display_name, l.entity_type, l.year
        FROM languages l
        WHERE l.id NOT IN (SELECT DISTINCT root_language_id FROM language_ancestry)
          AND l.id NOT IN (SELECT DISTINCT root_language_id FROM language_descendants)
          AND l.id NOT IN (SELECT DISTINCT ancestor_language_id FROM language_ancestry)
          AND l.id NOT IN (SELECT DISTINCT descendant_language_id FROM language_descendants)
        ORDER BY l.year ASC, l.name ASC
        """
    ).fetchall()
    orphans = [row_to_language(row) for row in rows]
    return {
        "generated_at": generated_at(),
        "count": len(orphans),
        "orphans": orphans,
    }


def build_influence_expanded(
    conn: sqlite3.Connection, summary: dict[str, Any]
) -> dict[str, Any]:
    scores = lineage_scores(summary)
    rows = conn.execute(
        """
        SELECT
            source.name AS source,
            source.display_name AS source_display_name,
            source.entity_type AS source_entity_type,
            source.year AS source_year,
            target.name AS target,
            target.display_name AS target_display_name,
            target.entity_type AS target_entity_type,
            target.year AS target_year,
            COALESCE(i.influence_type, 'direct') AS influence_type
        FROM influences i
        JOIN languages source ON source.id = i.source_id
        JOIN languages target ON target.id = i.target_id
        ORDER BY source.name, target.name
        """
    ).fetchall()

    nodes_by_name: dict[str, dict[str, Any]] = {}
    edges = []
    for row in rows:
        source_score = scores.get(row["source"], {})
        target_score = scores.get(row["target"], {})
        edges.append(
            {
                "source": row["source"],
                "source_entity_type": row["source_entity_type"],
                "target": row["target"],
                "target_entity_type": row["target_entity_type"],
                "influence_type": row["influence_type"],
                "source_reachability_score": source_score.get(
                    "reachability_score", 0
                ),
                "target_reachable_by_score": target_score.get(
                    "reachable_by_score", 0
                ),
            }
        )
        if row["source"] not in nodes_by_name:
            nodes_by_name[row["source"]] = {
                "name": row["source"],
                "display_name": row["source_display_name"] or row["source"],
                "entity_type": row["source_entity_type"],
                "year": row["source_year"],
                "reachability_score": source_score.get("reachability_score", 0),
            }
        if row["target"] not in nodes_by_name:
            nodes_by_name[row["target"]] = {
                "name": row["target"],
                "display_name": row["target_display_name"] or row["target"],
                "entity_type": row["target_entity_type"],
                "year": row["target_year"],
                "reachability_score": target_score.get("reachability_score", 0),
            }

    nodes = sorted(nodes_by_name.values(), key=lambda value: value["name"])
    return {
        "generated_at": generated_at(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


def build_auto_odyssey_candidates(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT l.name, l.display_name, l.year,
               COUNT(ld.descendant_language_id) AS direct_descendant_count,
               (SELECT COUNT(*) FROM language_descendants ld2
                WHERE ld2.root_language_id = l.id) AS total_descendant_count
        FROM languages l
        JOIN language_descendants ld ON ld.root_language_id = l.id AND ld.depth = 1
        WHERE l.entity_type = 'language'
        GROUP BY l.id
        HAVING direct_descendant_count >= 3
        ORDER BY total_descendant_count DESC
        LIMIT 20
        """
    ).fetchall()

    candidates = [
        {
            "name": row["name"],
            "display_name": row["display_name"] or row["name"],
            "year": row["year"],
            "direct_descendant_count": row["direct_descendant_count"],
            "total_descendant_count": row["total_descendant_count"],
        }
        for row in rows
    ]
    return {
        "generated_at": generated_at(),
        "count": len(candidates),
        "candidates": candidates,
    }


def generate_derived_data(
    db_path: str | os.PathLike[str] = DEFAULT_DB_PATH,
    out_dir: str | os.PathLike[str] = DEFAULT_OUT_DIR,
) -> list[Path]:
    db = Path(db_path)
    output_root = Path(out_dir)
    if not db.exists():
        raise FileNotFoundError(f"Database not found at {db}")

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        summary = build_lineage_summary(conn)
        artifacts = {
            Path("closure/language-lineage-summary.json"): summary,
            Path("reports/keystone-entities.json"): build_keystone_entities(
                conn, summary
            ),
            Path("reports/bridge-entities.json"): build_bridge_entities(conn),
            Path("reports/orphan-subgraphs.json"): build_orphan_subgraphs(conn),
            Path("viz/influence-expanded.json"): build_influence_expanded(
                conn, summary
            ),
            Path("odyssey/auto-odyssey-candidates.json"): build_auto_odyssey_candidates(
                conn
            ),
        }
        created: list[Path] = []
        for relative_path, payload in artifacts.items():
            path = output_root / relative_path
            write_json(path, payload)
            created.append(path)
        for subdir in ("search",):
            (output_root / subdir).mkdir(parents=True, exist_ok=True)
        return created
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate derived Atlas JSON data")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="Path to SQLite database",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT_DIR),
        help="Output root directory",
    )
    args = parser.parse_args(argv)

    try:
        generate_derived_data(args.db, args.out)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
