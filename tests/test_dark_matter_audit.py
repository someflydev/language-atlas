import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from scripts.dark_matter_audit import (  # noqa: E402
    DarkMatterConfigError,
    DarkMatterResolver,
    collect_dark_matter,
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_alias_resolution_python_and_javascript() -> None:
    resolver = DarkMatterResolver.from_data_dir(REPO_ROOT / "data")

    python_term = resolver.resolve("python (current state)", "entities")
    javascript_term = resolver.resolve("javascript (node.js - 2009)", "entities")

    assert python_term.display_term == "Python"
    assert python_term.bucket == "languages"
    assert javascript_term.display_term == "JavaScript"
    assert javascript_term.bucket == "languages"


def test_alias_resolution_shell_variants() -> None:
    resolver = DarkMatterResolver.from_data_dir(REPO_ROOT / "data")

    for term in ["sh", "Shell", "sh (Bourne shell)"]:
        resolved = resolver.resolve(term, "entities")
        assert resolved.display_term == "Bourne Shell"
        assert resolved.bucket == "languages"


def test_type_override_routes_canonical_term_to_language_bucket(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_json(
        data_dir / ".dark_matter_canonicals.json",
        {"Python": {"type": "language"}},
    )
    write_json(
        data_dir / ".dark_matter_aliases.json",
        {"python (current state)": "Python"},
    )

    resolver = DarkMatterResolver.from_data_dir(data_dir)
    resolved = resolver.resolve("python (current state)", "entities")

    assert resolved.display_term == "Python"
    assert resolved.bucket == "languages"


def test_validation_failure_for_missing_canonical_target(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_json(data_dir / ".dark_matter_canonicals.json", {})
    write_json(
        data_dir / ".dark_matter_aliases.json",
        {"python (current state)": "Python"},
    )

    with pytest.raises(DarkMatterConfigError, match="missing canonical target 'Python'"):
        DarkMatterResolver.from_data_dir(data_dir)


def test_validation_failure_for_normalized_alias_collision(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_json(
        data_dir / ".dark_matter_canonicals.json",
        {
            "Bourne Shell": {"type": "language"},
            "Python": {"type": "language"},
        },
    )
    write_json(
        data_dir / ".dark_matter_aliases.json",
        {
            "Shell": "Bourne Shell",
            "shell": "Python",
        },
    )

    with pytest.raises(DarkMatterConfigError, match="Alias keys collide after normalization"):
        DarkMatterResolver.from_data_dir(data_dir)


def test_profile_key_matches_existing_profile_stem(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = data_dir / "docs"

    write_json(
        data_dir / ".dark_matter_canonicals.json",
        {
            "Garmisch Conference": {
                "type": "historical_event",
                "profile_key": "garmisch_conference",
            }
        },
    )
    write_json(
        data_dir / ".dark_matter_aliases.json",
        {"Birth of Software Engineering": "Garmisch Conference"},
    )
    write_json(data_dir / "languages.json", [])
    write_json(data_dir / "people.json", [])
    write_json(data_dir / "concepts.json", [])
    write_json(
        data_dir / "eras.json",
        [
            {
                "name": "Software Era",
                "key_drivers": [],
                "pivotal_languages": [],
                "reactions_and_legacy": "",
                "crossroads": [
                    {
                        "title": "Birth of Software Engineering",
                        "key_players": [],
                        "related_languages": [],
                        "explanation": "",
                    }
                ],
            }
        ],
    )
    write_json(data_dir / "paradigms.json", [])
    write_json(
        docs_dir / "historical_events" / "garmisch_conference.json",
        {
            "title": "Garmisch Conference",
            "date": "1968",
            "overview": "Conference",
            "impact_on_computing": [],
            "key_figures": [],
            "legacy": [],
            "ai_assisted_discovery_missions": [],
        },
    )

    todo = collect_dark_matter(data_dir)

    assert "Garmisch Conference" not in todo["missing_historical_events"]
