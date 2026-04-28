import sqlite3
import time

from app.core.build_sqlite import _populate_closure_tables


PRIMARY_NAMES = {
    1: "Root",
    2: "Alpha",
    3: "Beta",
    4: "Gamma",
    5: "Delta",
    6: "Island",
    7: "Omega",
}

PRIMARY_EDGES = [
    (1, 2),
    (1, 3),
    (2, 3),
    (2, 4),
    (3, 7),
    (4, 5),
    (5, 7),
]


def make_test_db(
    edges: list[tuple[int, int]],
    n_languages: int,
    names: dict[int, str] | None = None,
) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE languages (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE influences (
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            influence_type TEXT,
            PRIMARY KEY (source_id, target_id)
        );

        CREATE TABLE language_ancestry (
            root_language_id    INTEGER NOT NULL,
            ancestor_language_id INTEGER NOT NULL,
            depth               INTEGER NOT NULL,
            path_count          INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (root_language_id, ancestor_language_id)
        );

        CREATE TABLE language_descendants (
            root_language_id       INTEGER NOT NULL,
            descendant_language_id INTEGER NOT NULL,
            depth                  INTEGER NOT NULL,
            path_count             INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (root_language_id, descendant_language_id)
        );

        CREATE TABLE language_reachability (
            from_language_id INTEGER NOT NULL,
            to_language_id   INTEGER NOT NULL,
            min_depth        INTEGER NOT NULL,
            path_count       INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (from_language_id, to_language_id)
        );

        CREATE TABLE language_lineage_paths_bounded (
            from_language_id INTEGER NOT NULL,
            to_language_id   INTEGER NOT NULL,
            depth            INTEGER NOT NULL,
            path_text        TEXT NOT NULL,
            edge_types_text  TEXT
        );
        """
    )

    language_rows = [
        (language_id, (names or {}).get(language_id, f"L{language_id}"))
        for language_id in range(1, n_languages + 1)
    ]
    cursor.executemany("INSERT INTO languages (id, name) VALUES (?, ?)", language_rows)
    cursor.executemany(
        """
        INSERT INTO influences (source_id, target_id, influence_type)
        VALUES (?, ?, NULL)
        """,
        edges,
    )

    _populate_closure_tables(conn, cursor)
    return conn


def primary_conn() -> sqlite3.Connection:
    return make_test_db(PRIMARY_EDGES, 7, PRIMARY_NAMES)


def test_synthetic_ancestry_correctness() -> None:
    conn = primary_conn()

    root_ancestor_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_ancestry
        WHERE root_language_id = 1
        """
    ).fetchone()["count"]
    omega_ancestors = {
        row["ancestor_language_id"]
        for row in conn.execute(
            """
            SELECT ancestor_language_id
            FROM language_ancestry
            WHERE root_language_id = 7
            """
        )
    }
    alpha_ancestors = [
        row["ancestor_language_id"]
        for row in conn.execute(
            """
            SELECT ancestor_language_id
            FROM language_ancestry
            WHERE root_language_id = 2
            """
        )
    ]
    omega_root = conn.execute(
        """
        SELECT depth, path_count
        FROM language_ancestry
        WHERE root_language_id = 7
          AND ancestor_language_id = 1
        """
    ).fetchone()

    assert root_ancestor_count == 0
    assert omega_ancestors == {1, 2, 3, 4, 5}
    assert alpha_ancestors == [1]
    assert omega_root["depth"] == 2
    assert omega_root["path_count"] >= 2

    conn.close()


def test_synthetic_descendant_correctness() -> None:
    conn = primary_conn()

    root_descendants = {
        row["descendant_language_id"]
        for row in conn.execute(
            """
            SELECT descendant_language_id
            FROM language_descendants
            WHERE root_language_id = 1
            """
        )
    }
    island_descendant_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_descendants
        WHERE root_language_id = 6
        """
    ).fetchone()["count"]
    delta_descendants = [
        row["descendant_language_id"]
        for row in conn.execute(
            """
            SELECT descendant_language_id
            FROM language_descendants
            WHERE root_language_id = 5
            """
        )
    ]
    root_depths = {
        row["descendant_language_id"]: row["depth"]
        for row in conn.execute(
            """
            SELECT descendant_language_id, depth
            FROM language_descendants
            WHERE root_language_id = 1
            """
        )
    }
    self_reference_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_descendants
        WHERE root_language_id = descendant_language_id
        """
    ).fetchone()["count"]

    assert root_descendants == {2, 3, 4, 5, 7}
    assert island_descendant_count == 0
    assert delta_descendants == [7]
    assert root_depths[2] == 1
    assert root_depths[4] == 2
    assert root_depths[7] == 2
    assert self_reference_count == 0

    conn.close()


def test_synthetic_reachability_correctness() -> None:
    conn = primary_conn()

    descendant_count = conn.execute(
        "SELECT COUNT(*) AS count FROM language_descendants"
    ).fetchone()["count"]
    reachability_count = conn.execute(
        "SELECT COUNT(*) AS count FROM language_reachability"
    ).fetchone()["count"]
    root_to_omega = conn.execute(
        """
        SELECT min_depth
        FROM language_reachability
        WHERE from_language_id = 1
          AND to_language_id = 7
        """
    ).fetchone()
    island_related_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_reachability
        WHERE from_language_id = 6
           OR to_language_id = 6
        """
    ).fetchone()["count"]
    alpha_to_beta = conn.execute(
        """
        SELECT min_depth
        FROM language_reachability
        WHERE from_language_id = 2
          AND to_language_id = 3
        """
    ).fetchone()
    mismatches = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_descendants d
        LEFT JOIN language_reachability r
          ON r.from_language_id = d.root_language_id
         AND r.to_language_id = d.descendant_language_id
         AND r.min_depth = d.depth
         AND r.path_count = d.path_count
        WHERE r.from_language_id IS NULL
        """
    ).fetchone()["count"]

    assert reachability_count == descendant_count
    assert root_to_omega["min_depth"] == 2
    assert island_related_count == 0
    assert alpha_to_beta["min_depth"] == 1
    assert mismatches == 0

    conn.close()


def test_cycle_safety_and_bounded_reachability() -> None:
    start = time.perf_counter()
    conn = make_test_db([(1, 2), (2, 3), (3, 1), (4, 1)], 4, {
        1: "C1",
        2: "C2",
        3: "C3",
        4: "C4",
    })
    elapsed = time.perf_counter() - start

    self_ancestor_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_ancestry
        WHERE root_language_id = ancestor_language_id
        """
    ).fetchone()["count"]
    self_descendant_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_descendants
        WHERE root_language_id = descendant_language_id
        """
    ).fetchone()["count"]
    c4_descendant_depths = {
        row["descendant_language_id"]: row["depth"]
        for row in conn.execute(
            """
            SELECT descendant_language_id, depth
            FROM language_descendants
            WHERE root_language_id = 4
            """
        )
    }
    cycle_descendants = {
        root_id: {
            row["descendant_language_id"]
            for row in conn.execute(
                """
                SELECT descendant_language_id
                FROM language_descendants
                WHERE root_language_id = ?
                """,
                (root_id,),
            )
        }
        for root_id in (1, 2, 3)
    }
    cycle_ancestors = {
        root_id: {
            row["ancestor_language_id"]
            for row in conn.execute(
                """
                SELECT ancestor_language_id
                FROM language_ancestry
                WHERE root_language_id = ?
                """,
                (root_id,),
            )
        }
        for root_id in (1, 2, 3)
    }
    cycle_descendant_depths = {
        (row["root_language_id"], row["descendant_language_id"]): row["depth"]
        for row in conn.execute(
            """
            SELECT root_language_id, descendant_language_id, depth
            FROM language_descendants
            WHERE root_language_id IN (1, 2, 3)
            """
        )
    }
    cycle_ancestor_depths = {
        (row["root_language_id"], row["ancestor_language_id"]): row["depth"]
        for row in conn.execute(
            """
            SELECT root_language_id, ancestor_language_id, depth
            FROM language_ancestry
            WHERE root_language_id IN (1, 2, 3)
            """
        )
    }

    assert elapsed < 5
    assert self_ancestor_count == 0
    assert self_descendant_count == 0
    assert c4_descendant_depths[1] == 1
    assert c4_descendant_depths[2] == 2
    assert c4_descendant_depths[3] == 3
    assert cycle_descendants == {
        1: {2, 3},
        2: {1, 3},
        3: {1, 2},
    }
    assert cycle_ancestors == {
        1: {2, 3, 4},
        2: {1, 3, 4},
        3: {1, 2, 4},
    }
    assert cycle_descendant_depths[(1, 2)] == 1
    assert cycle_descendant_depths[(1, 3)] == 2
    assert cycle_descendant_depths[(2, 3)] == 1
    assert cycle_descendant_depths[(2, 1)] == 2
    assert cycle_descendant_depths[(3, 1)] == 1
    assert cycle_descendant_depths[(3, 2)] == 2
    assert cycle_ancestor_depths[(1, 3)] == 1
    assert cycle_ancestor_depths[(1, 2)] == 2
    assert cycle_ancestor_depths[(2, 1)] == 1
    assert cycle_ancestor_depths[(2, 3)] == 2
    assert cycle_ancestor_depths[(3, 2)] == 1
    assert cycle_ancestor_depths[(3, 1)] == 2

    conn.close()


def test_depth_limit_for_linear_chain() -> None:
    conn = make_test_db([(node_id, node_id + 1) for node_id in range(1, 15)], 15)

    l1_descendants = {
        row["descendant_language_id"]
        for row in conn.execute(
            """
            SELECT descendant_language_id
            FROM language_descendants
            WHERE root_language_id = 1
            """
        )
    }
    max_depth = conn.execute(
        "SELECT MAX(depth) AS max_depth FROM language_descendants"
    ).fetchone()["max_depth"]

    assert set(range(2, 12)) <= l1_descendants
    assert not set(range(12, 16)) & l1_descendants
    assert max_depth == 10
    assert 1 not in l1_descendants

    conn.close()


def test_path_text_matches_bounded_paths() -> None:
    conn = primary_conn()

    path_rows = conn.execute(
        """
        SELECT p.from_language_id, p.to_language_id, p.path_text,
               source.name AS source_name, target.name AS target_name
        FROM language_lineage_paths_bounded p
        JOIN languages source ON source.id = p.from_language_id
        JOIN languages target ON target.id = p.to_language_id
        """
    ).fetchall()

    assert path_rows
    for row in path_rows:
        tokens = row["path_text"].split(" -> ")
        assert " -> " in row["path_text"]
        assert tokens[0] == row["source_name"]
        assert tokens[-1] == row["target_name"]
        assert len(tokens) == len(set(tokens))

    conn.close()
