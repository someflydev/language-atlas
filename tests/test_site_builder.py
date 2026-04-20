"""Tests for src/app/core/site_builder.py.

Requires language_atlas.sqlite to exist (run `make build` if absent).
Tests use tmp_path so they never pollute the real generated-docs/ directory.
"""

import os
from pathlib import Path

import pytest

from app.core.data_loader import DataLoader
from app.core.site_builder import SiteBuilder


def _make_loader() -> DataLoader:
    os.environ.setdefault("USE_SQLITE", "1")
    return DataLoader()


def test_site_builder_runs_against_live_db(tmp_path: Path) -> None:
    """SiteBuilder.build_markdown() completes without raising exceptions."""
    loader = _make_loader()
    SiteBuilder(loader, tmp_path).build_markdown()


def test_site_builder_emits_index_and_readme(tmp_path: Path) -> None:
    """INDEX.md and README.md exist after build and contain required headings."""
    loader = _make_loader()
    SiteBuilder(loader, tmp_path).build_markdown()

    index = (tmp_path / "INDEX.md").read_text(encoding="utf-8")
    assert (tmp_path / "README.md").exists()
    assert "## Browse" in index
    assert "## Highlights" in index
    assert "## Eras at a glance" in index
    assert "## Counts" in index


def test_site_builder_language_count_matches_loader(tmp_path: Path) -> None:
    """Number of language files equals loader.get_all_languages()."""
    loader = _make_loader()
    SiteBuilder(loader, tmp_path).build_markdown()

    expected = len(loader.get_all_languages(entity_type=None))
    actual = len(list((tmp_path / "languages").glob("*.md")))
    assert actual == expected


def test_site_builder_concept_count_matches_loader(tmp_path: Path) -> None:
    """Number of concept files equals loader.get_all_concepts()."""
    loader = _make_loader()
    SiteBuilder(loader, tmp_path).build_markdown()

    expected = len(loader.get_all_concepts())
    actual = len(list((tmp_path / "concepts").glob("*.md")))
    assert actual == expected


def test_site_builder_no_raw_sql(tmp_path: Path) -> None:
    """site_builder.py must contain no raw conn.execute( calls."""
    src = Path(__file__).parent.parent / "src" / "app" / "core" / "site_builder.py"
    content = src.read_text(encoding="utf-8")
    assert "conn.execute(" not in content
