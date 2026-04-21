import json

from typer.testing import CliRunner

import cli as atlas_cli
from tui import LivingAtlasApp


runner = CliRunner()


class FakeCliLoader:
    use_sqlite = False
    languages = []

    def get_paradigm_ecosystem(self, name: str):
        if name != "Functional":
            return {"paradigm": {}, "foundations": [], "languages": [], "stats": {}}
        return {
            "paradigm": {
                "name": "Functional",
                "description": "Computation by function evaluation.",
            },
            "foundations": [
                {
                    "name": "Lambda Calculus",
                    "display_name": "Lambda Calculus",
                    "entity_type": "foundation",
                    "relevance_reason": "Tagged with Functional and upstream of 2 Functional languages",
                    "supporting_language_count": 2,
                    "example_languages": ["ML", "Haskell"],
                    "is_directly_tagged": True,
                }
            ],
            "languages": [
                {
                    "name": "Haskell",
                    "display_name": "Haskell",
                    "entity_type": "language",
                    "year": 1990,
                    "cluster": "academic",
                    "paradigms": ["Functional"],
                }
            ],
            "stats": {
                "language_count": 1,
                "foundation_count": 1,
                "earliest_language_year": 1990,
                "earliest_foundation_year": 1930,
            },
        }

    def get_influences(self, name: str):
        return {
            "influenced_by": ["Lambda Calculus", "ML"],
            "influenced": ["Elm"],
            "influenced_by_details": [
                {
                    "name": "Lambda Calculus",
                    "display_name": "Lambda Calculus",
                    "entity_type": "foundation",
                    "type": "formal-foundation",
                },
                {
                    "name": "ML",
                    "display_name": "ML",
                    "entity_type": "language",
                    "type": "direct",
                },
            ],
            "influenced_details": [
                {
                    "name": "Elm",
                    "display_name": "Elm",
                    "entity_type": "language",
                    "type": "inspired",
                }
            ],
            "upstream_influence_groups": [
                {
                    "key": "foundational_precursors",
                    "label": "Foundational Precursors",
                    "items": [
                        {
                            "name": "Lambda Calculus",
                            "display_name": "Lambda Calculus",
                            "entity_type": "foundation",
                            "type": "formal-foundation",
                        }
                    ],
                },
                {
                    "key": "language_ancestors",
                    "label": "Language Ancestors",
                    "items": [
                        {
                            "name": "ML",
                            "display_name": "ML",
                            "entity_type": "language",
                            "type": "direct",
                        }
                    ],
                },
            ],
        }

    def get_language(self, name: str):
        return {
            "name": name,
            "display_name": name,
            "entity_type": "language",
            "year": 2004,
            "cluster": "academic",
            "generation": "renaissance",
            "key_innovations": ["Typeclasses"],
            "philosophy": "A terse philosophy entry.",
        }


class FakeTuiLoader:
    def get_all_languages(self, entity_type="language"):
        items = [
            {
                "name": "Haskell",
                "display_name": "Haskell",
                "entity_type": "language",
                "generation": "renaissance",
                "year": 1990,
            },
            {
                "name": "Lambda Calculus",
                "display_name": "Lambda Calculus",
                "entity_type": "foundation",
                "generation": "early",
                "year": 1930,
            },
            {
                "name": "JVM",
                "display_name": "JVM",
                "entity_type": "artifact",
                "generation": "web1",
                "year": 1995,
            },
        ]
        if entity_type is None:
            return items
        return [item for item in items if item["entity_type"] == entity_type]

    def get_influences(self, name: str):
        return {
            "upstream_influence_groups": [
                {
                    "key": "foundational_precursors",
                    "label": "Foundational Precursors",
                    "items": [
                        {
                            "name": "Lambda Calculus",
                            "display_name": "Lambda Calculus",
                            "entity_type": "foundation",
                            "type": "formal-foundation",
                        }
                    ],
                },
                {
                    "key": "language_ancestors",
                    "label": "Language Ancestors",
                    "items": [
                        {
                            "name": "ML",
                            "display_name": "ML",
                            "entity_type": "language",
                            "type": "direct",
                        }
                    ],
                },
            ],
            "influenced_details": [
                {
                    "name": "Elm",
                    "display_name": "Elm",
                    "entity_type": "language",
                    "type": "inspired",
                }
            ],
        }

    def get_combined_language_data(self, name: str):
        return {
            "name": name,
            "display_name": name,
            "year": 2004,
            "entity_type": "language",
            "creators": ["Martin Odersky"],
            "paradigms": ["Functional", "Object-Oriented"],
            "cluster": "academic",
            "generation": "renaissance",
            "overview": "A hybrid language profile.",
            "philosophy": "Composable abstractions.",
            "mental_model": "Functions plus objects.",
            "key_innovations": ["Typeclasses"],
            "historical_context": "Built on JVM lessons.",
            **self.get_influences(name),
        }


def test_cli_paradigm_command_renders_foundations_and_languages(monkeypatch):
    monkeypatch.setattr(atlas_cli, "get_loader", lambda: FakeCliLoader())

    result = runner.invoke(atlas_cli.app, ["paradigm", "Functional"])

    assert result.exit_code == 0
    assert "Foundational Precursors" in result.stdout
    assert "Languages in this paradigm" in result.stdout
    assert "Lambda Calculus" in result.stdout
    assert "Haskell" in result.stdout


def test_cli_paradigm_command_supports_json(monkeypatch):
    monkeypatch.setattr(atlas_cli, "get_loader", lambda: FakeCliLoader())

    result = runner.invoke(atlas_cli.app, ["paradigm", "Functional", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["paradigm"]["name"] == "Functional"
    assert payload["foundations"][0]["name"] == "Lambda Calculus"
    assert payload["languages"][0]["name"] == "Haskell"


def test_cli_influences_renders_grouped_upstream_sections(monkeypatch):
    monkeypatch.setattr(atlas_cli, "get_loader", lambda: FakeCliLoader())

    result = runner.invoke(atlas_cli.app, ["influences", "Scala"])

    assert result.exit_code == 0
    assert "Foundational Precursors" in result.stdout
    assert "Language Ancestors" in result.stdout
    assert "Downstream Influences" in result.stdout
    assert "Lambda Calculus" in result.stdout
    assert "ML" in result.stdout


def test_tui_reader_markdown_uses_grouped_lineage_sections():
    app = LivingAtlasApp()
    app.loader = FakeTuiLoader()

    markdown = app.generate_markdown(app.loader.get_combined_language_data("Scala"))

    assert "## Upstream Lineage" in markdown
    assert "### Foundational Precursors" in markdown
    assert "### Language Ancestors" in markdown
    assert "Lambda Calculus (Foundation, formal-foundation)" in markdown
    assert "### Downstream Influences" in markdown


def test_tui_nexus_sections_use_grouped_lineage():
    app = LivingAtlasApp()
    app.loader = FakeTuiLoader()

    sections = app.get_nexus_sections("Scala")

    assert [section["label"] for section in sections] == [
        "Foundational Precursors",
        "Language Ancestors",
        "Downstream Influences",
    ]
    assert sections[0]["items"][0]["name"] == "Lambda Calculus"
    assert sections[1]["items"][0]["name"] == "ML"


def test_tui_browse_mode_exposes_foundations_and_artifacts():
    app = LivingAtlasApp()
    app.loader = FakeTuiLoader()

    assert [item["name"] for item in app.get_browse_entities_for_mode("language")] == ["Haskell"]
    assert [item["name"] for item in app.get_browse_entities_for_mode("foundation")] == ["Lambda Calculus"]
    assert [item["name"] for item in app.get_browse_entities_for_mode("artifact")] == ["JVM"]
