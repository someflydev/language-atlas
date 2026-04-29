import importlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "language_atlas.sqlite"
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

generate_derived_data = importlib.import_module("generate_derived_data")


pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason="language_atlas.sqlite is not available; run make build first",
)


EXPECTED_FILES = [
    Path("closure/language-lineage-summary.json"),
    Path("reports/keystone-entities.json"),
    Path("reports/bridge-entities.json"),
    Path("reports/orphan-subgraphs.json"),
    Path("viz/influence-expanded.json"),
    Path("odyssey/auto-odyssey-candidates.json"),
]


@pytest.fixture
def derived_output(tmp_path: Path) -> Path:
    generate_derived_data.generate_derived_data(DB_PATH, tmp_path)
    return tmp_path


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def test_script_is_importable() -> None:
    assert hasattr(generate_derived_data, "generate_derived_data")


def test_files_are_written(derived_output: Path) -> None:
    for relative_path in EXPECTED_FILES:
        assert (derived_output / relative_path).is_file()


def test_lineage_summary_schema(derived_output: Path) -> None:
    data = read_json(derived_output / "closure/language-lineage-summary.json")

    assert data["generated_at"]
    assert data["language_count"] > 0
    assert data["languages"]

    expected_keys = {
        "name",
        "display_name",
        "entity_type",
        "year",
        "ancestor_count",
        "descendant_count",
        "max_ancestor_depth",
        "max_descendant_depth",
        "reachability_score",
        "reachable_by_score",
    }
    assert expected_keys <= set(data["languages"][0])


def test_keystone_entities_non_empty(derived_output: Path) -> None:
    data = read_json(derived_output / "reports/keystone-entities.json")

    assert data["keystones"]
    assert any(item["keystone_score"] > 0 for item in data["keystones"])
    assert all(
        item["keystone_score"] > 0 or item["is_keystone_flag"]
        for item in data["keystones"]
    )


def test_keystone_entities_include_zero_score_flags(derived_output: Path) -> None:
    data = read_json(derived_output / "reports/keystone-entities.json")
    keystone_names = {item["name"] for item in data["keystones"]}

    assert {
        "Jacquard Loom",
        "Lambda Calculus",
        "Mathematical Notation",
    } <= keystone_names


def test_no_orphans_are_also_keystones(derived_output: Path) -> None:
    orphans = read_json(derived_output / "reports/orphan-subgraphs.json")
    keystones = read_json(derived_output / "reports/keystone-entities.json")

    orphan_names = {item["name"] for item in orphans["orphans"]}
    keystone_names = {item["name"] for item in keystones["keystones"]}

    assert orphan_names.isdisjoint(keystone_names)


def test_odyssey_candidates(derived_output: Path) -> None:
    data = read_json(derived_output / "odyssey/auto-odyssey-candidates.json")

    assert 0 < data["count"] <= 20
    assert all(
        item["direct_descendant_count"] >= 3 for item in data["candidates"]
    )
    candidates_with_steps = [
        item for item in data["candidates"] if item.get("steps")
    ]
    assert candidates_with_steps
    for candidate in candidates_with_steps:
        assert len(candidate["steps"]) <= 4
        for step in candidate["steps"]:
            assert {"language", "display_name", "milestone"} <= set(step)
            assert step["language"]
            assert step["display_name"]
            assert step["milestone"]
