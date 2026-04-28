import sqlite3

from app.core.data_loader import DataLoader


def test_closure_table_schema(db_conn: sqlite3.Connection) -> None:
    expected_columns = {
        "language_ancestry": {
            "root_language_id",
            "ancestor_language_id",
            "depth",
            "path_count",
        },
        "language_descendants": {
            "root_language_id",
            "descendant_language_id",
            "depth",
            "path_count",
        },
        "language_reachability": {
            "from_language_id",
            "to_language_id",
            "min_depth",
            "path_count",
        },
        "language_lineage_paths_bounded": {
            "from_language_id",
            "to_language_id",
            "depth",
            "path_text",
            "edge_types_text",
        },
    }

    for table, columns in expected_columns.items():
        row = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()
        assert row is not None

        actual_columns = {
            column["name"]
            for column in db_conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        assert columns <= actual_columns


def test_language_ancestry_contains_direct_influencer(db_conn: sqlite3.Connection) -> None:
    edge = db_conn.execute(
        """
        SELECT source_id, target_id
        FROM influences
        ORDER BY source_id, target_id
        LIMIT 1
        """
    ).fetchone()
    assert edge is not None

    row = db_conn.execute(
        """
        SELECT depth, path_count
        FROM language_ancestry
        WHERE root_language_id = ?
          AND ancestor_language_id = ?
        """,
        (edge["target_id"], edge["source_id"]),
    ).fetchone()

    assert row is not None
    assert row["depth"] >= 1
    assert row["path_count"] >= 1


def test_language_descendants_contains_direct_descendant(db_conn: sqlite3.Connection) -> None:
    edge = db_conn.execute(
        """
        SELECT source_id, target_id
        FROM influences
        ORDER BY source_id, target_id
        LIMIT 1
        """
    ).fetchone()
    assert edge is not None

    row = db_conn.execute(
        """
        SELECT depth, path_count
        FROM language_descendants
        WHERE root_language_id = ?
          AND descendant_language_id = ?
        """,
        (edge["source_id"], edge["target_id"]),
    ).fetchone()

    assert row is not None
    assert row["depth"] == 1
    assert row["path_count"] >= 1


def test_closure_tables_are_depth_limited_and_cycle_safe(db_conn: sqlite3.Connection) -> None:
    checks = (
        ("language_ancestry", "depth"),
        ("language_descendants", "depth"),
        ("language_reachability", "min_depth"),
        ("language_lineage_paths_bounded", "depth"),
    )
    for table, depth_column in checks:
        row = db_conn.execute(
            f"SELECT COUNT(*) AS count FROM {table} WHERE {depth_column} > 10"
        ).fetchone()
        assert row["count"] == 0

    self_ancestor_count = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_ancestry
        WHERE root_language_id = ancestor_language_id
        """
    ).fetchone()
    assert self_ancestor_count["count"] == 0

    self_descendant_count = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_descendants
        WHERE root_language_id = descendant_language_id
        """
    ).fetchone()
    assert self_descendant_count["count"] == 0


def test_live_closure_tables_exist_and_are_non_empty(db_conn: sqlite3.Connection) -> None:
    for table in (
        "language_ancestry",
        "language_descendants",
        "language_reachability",
        "language_lineage_paths_bounded",
    ):
        table_row = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()
        count_row = db_conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()

        assert table_row is not None
        assert count_row["count"] > 0


def test_live_closure_depths_are_bounded(db_conn: sqlite3.Connection) -> None:
    checks = (
        ("language_ancestry", "depth"),
        ("language_descendants", "depth"),
        ("language_reachability", "min_depth"),
        ("language_lineage_paths_bounded", "depth"),
    )

    for table, depth_column in checks:
        out_of_bounds = db_conn.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM {table}
            WHERE {depth_column} < 1
               OR {depth_column} > 10
            """
        ).fetchone()
        assert out_of_bounds["count"] == 0


def test_live_high_influence_language_has_descendants(db_conn: sqlite3.Connection) -> None:
    c_language = db_conn.execute(
        "SELECT id FROM languages WHERE name = ?",
        ("C",),
    ).fetchone()
    assert c_language is not None

    descendant_count = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_descendants
        WHERE root_language_id = ?
        """,
        (c_language["id"],),
    ).fetchone()

    assert descendant_count["count"] > 1


def test_live_keystone_language_has_multiple_descendants(db_conn: sqlite3.Connection) -> None:
    keystone = db_conn.execute(
        """
        SELECT id
        FROM languages
        WHERE name IN ('LISP', 'C', 'ALGOL 60')
        ORDER BY CASE name
            WHEN 'LISP' THEN 1
            WHEN 'C' THEN 2
            WHEN 'ALGOL 60' THEN 3
            ELSE 4
        END
        LIMIT 1
        """
    ).fetchone()
    assert keystone is not None

    descendant_count = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_descendants
        WHERE root_language_id = ?
        """,
        (keystone["id"],),
    ).fetchone()

    assert descendant_count["count"] >= 3


def test_dataloader_uses_closure_tables(mock_loader: DataLoader) -> None:
    language = mock_loader.get_language("Python")
    assert language is not None

    ancestors = mock_loader.get_ancestors(language["id"], max_depth=5)
    descendants = mock_loader.get_descendants(language["id"], max_depth=5)

    assert ancestors
    assert descendants
    for item in ancestors + descendants:
        assert {"name", "depth", "entity_type", "path_count"} <= set(item)
        assert item["path_count"] >= 1


def test_reachability_populated_from_descendants(db_conn: sqlite3.Connection) -> None:
    descendant_count = db_conn.execute(
        "SELECT COUNT(*) AS count FROM language_descendants"
    ).fetchone()
    reachability_count = db_conn.execute(
        "SELECT COUNT(*) AS count FROM language_reachability"
    ).fetchone()

    assert descendant_count["count"] > 0
    assert reachability_count["count"] == descendant_count["count"]
