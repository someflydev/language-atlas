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


def write_minimal_dark_matter_fixture(data_dir: Path) -> None:
    docs_dir = data_dir / "docs"
    for directory in [
        "language_profiles",
        "concept_profiles",
        "org_profiles",
        "historical_events",
        "people_profiles",
        "atlas_meta",
        "concept_combos",
    ]:
        (docs_dir / directory).mkdir(parents=True, exist_ok=True)

    write_json(data_dir / ".dark_matter_aliases.json", {})
    write_json(data_dir / ".dark_matter_canonicals.json", {})
    write_json(data_dir / "people.json", [])
    write_json(data_dir / "languages.json", [])
    write_json(data_dir / "concepts.json", [])
    write_json(data_dir / "eras.json", [])
    write_json(data_dir / "paradigms.json", [])
    write_json(data_dir / "learning_paths.json", [])
    write_json(data_dir / "influences.json", [])


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


def test_alias_resolution_reviewed_language_variants() -> None:
    resolver = DarkMatterResolver.from_data_dir(REPO_ROOT / "data")

    cases = {
        "Algol 58": "ALGOL 58",
        "Assembly (Early 1940s)": "Assembly",
        "C#": "CSharp",
        "Crystal (The Reactions to the New Complexity)": "Crystal",
        "Erlang (1980s)": "Erlang",
        "F#": "FSharp",
        "Flow Matic": "FLOW-MATIC",
        "Forth (late 1960s onward)": "Forth",
        "GraphQL (internal from 2012; open-sourced 2015)": "GraphQL",
        "HCL (HashiCorp Configuration Language)": "HCL",
        "K (1990s)": "K",
        "Lua (1993 onward)": "Lua",
        "MATLAB (late 1970s onward)": "MATLAB",
        "Objective-C (early 1980s)": "Objective-C",
        "PowerShell (2006 onward)": "PowerShell",
        "Purescript": "PureScript",
        "R (1990s)": "R",
        "Rust (Mozilla era, 2009 onward)": "Rust",
        "Self (late 1980s)": "Self",
        "TypeScript (2012/2015 Surge)": "TypeScript",
        "VBNET": "VB.NET",
    }

    for term, expected in cases.items():
        resolved = resolver.resolve(term, "entities")
        assert resolved.display_term == expected
        assert resolved.bucket == "languages"


def test_alias_resolution_reviewed_organization_variants() -> None:
    resolver = DarkMatterResolver.from_data_dir(REPO_ROOT / "data")

    resolved = resolver.resolve("Google (industrial reformers)", "entities")

    assert resolved.display_term == "Google"
    assert resolved.bucket == "organizations"


def test_alias_resolution_reviewed_person_variants() -> None:
    resolver = DarkMatterResolver.from_data_dir(REPO_ROOT / "data")

    cases = {
        "Alick Glennie (Autocode pioneer)": "Alick Glennie",
        "Bjarne Stroustrup (C++ designer)": "Bjarne Stroustrup",
        "Guy Steele": "Guy L. Steele",
        "John McCarthy (LISP originator)": "John McCarthy",
        "John W. Mauchly": "John Mauchly",
        "Kenneth Iverson": "Kenneth E. Iverson",
        "Kristen Nygaard (abstraction innovators)": "Kristen Nygaard",
    }

    for term, expected in cases.items():
        resolved = resolver.resolve(term, "entities")
        assert resolved.display_term == expected
        assert resolved.bucket == "entities"


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


def test_concepts_responsible_contributes_referenced_entity(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_minimal_dark_matter_fixture(data_dir)
    write_json(
        data_dir / "concepts.json",
        [
            {
                "name": "Immutability",
                "description": "Concept text.",
                "responsible": ["John McCarthy"],
            }
        ],
    )

    todo = collect_dark_matter(data_dir)

    assert "John McCarthy" in todo["missing_entities"]


def test_era_narrative_fields_contribute_references(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_minimal_dark_matter_fixture(data_dir)
    write_json(
        data_dir / "eras.json",
        [
            {
                "name": "The Dawn of Computation",
                "description": "**Ada Lovelace** framed the Analytical Engine.",
                "catalyst": "WWII accelerated computing demand.",
                "key_innovations": ["Stored Program"],
                "timeline_events": [
                    {"description": "**Alan Turing** formalized the machine model."}
                ],
                "modern_reactions": ["Functional Revival"],
                "key_drivers": [],
                "pivotal_languages": [],
                "reactions_and_legacy": "",
                "crossroads": [],
            }
        ],
    )

    todo = collect_dark_matter(data_dir)

    assert "Ada Lovelace" in todo["missing_entities"]
    assert "Alan Turing" in todo["missing_entities"]
    assert "Stored Program" in todo["missing_entities"]


def test_paradigm_languages_contribute_language_references(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_minimal_dark_matter_fixture(data_dir)
    write_json(
        data_dir / "paradigms.json",
        [
            {
                "name": "Actor-model",
                "description": "Concurrent model.",
                "motivation": "Carl Hewitt responded to coordination failures.",
                "languages": ["Erlang"],
                "connected_paradigms": ["Reactive"],
                "key_features": {"The Reaction": "Asynchronous Message Passing"},
            }
        ],
    )

    todo = collect_dark_matter(data_dir)

    assert "Erlang" in todo["missing_language_profiles"]


def test_learning_paths_languages_contribute_language_references(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_minimal_dark_matter_fixture(data_dir)
    write_json(
        data_dir / "learning_paths.json",
        [
            {
                "id": "path",
                "title": "The Systems Descent",
                "description": "Trace memory safety.",
                "steps": [
                    {
                        "language": "Rust",
                        "milestone": "The Safety Revolution",
                        "rationale": "The Borrow Checker reshapes systems work.",
                        "challenge": "Refactor pointers.",
                    }
                ],
            }
        ],
    )

    todo = collect_dark_matter(data_dir)

    assert "Rust" in todo["missing_language_profiles"]


def test_era_summaries_are_scanned_but_atlas_meta_is_excluded(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    write_minimal_dark_matter_fixture(data_dir)
    write_json(
        data_dir / "docs" / "era_summaries" / "early.json",
        {
            "slug": "early",
            "title": "Early Era",
            "overview": "**Grace Hopper** pushed compilers toward practicality.",
        },
    )
    write_json(
        data_dir / "docs" / "atlas_meta" / "Guided_Odyssey.json",
        {
            "title": "Guided Odyssey",
            "overview": "**Atlas Meta Person** should remain excluded.",
        },
    )

    todo = collect_dark_matter(data_dir)

    assert "Grace Hopper" in todo["missing_entities"]
    assert "Atlas Meta Person" not in todo["missing_entities"]
