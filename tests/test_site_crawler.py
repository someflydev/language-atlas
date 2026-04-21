"""Tests for SiteCrawler in src/app/core/site_builder.py.

Requires language_atlas.sqlite to exist (run `make build` if absent).
The crawl runs once per test session via a session-scoped fixture.
"""

import os
import re
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from app import app as app_module
from app.core.data_loader import DataLoader
from app.core.site_builder import CrawlReport, SiteCrawler


def _make_loader() -> DataLoader:
    os.environ.setdefault("USE_SQLITE", "1")
    return DataLoader()


def _find_representative_paradigm(loader: DataLoader) -> tuple[str, dict] | None:
    for name in loader.get_all_paradigms():
        ecosystem = loader.get_paradigm_ecosystem(name)
        if ecosystem["foundations"] and ecosystem["languages"]:
            return name, ecosystem
    return None


@pytest.fixture(scope="session")
def crawled_site(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, CrawlReport, DataLoader]:
    """Run one full crawl into a shared session-scoped temp directory."""
    site_dir = tmp_path_factory.mktemp("site", numbered=False)
    loader = _make_loader()
    report = SiteCrawler(loader, site_dir).crawl()
    return site_dir, report, loader


def test_crawler_emits_index_html(crawled_site: tuple) -> None:
    """crawl() produces site/index.html that is non-empty."""
    site_dir, _, _ = crawled_site
    index = site_dir / "index.html"
    assert index.exists(), "index.html not written"
    assert index.stat().st_size > 0, "index.html is empty"


def test_crawler_emits_one_file_per_language(crawled_site: tuple) -> None:
    """One language/*/index.html is written for each language the crawler exports.

    The crawler enumerates language URLs from the entity link map, which
    may include languages without profiles (e.g. precursor systems like
    'Mathematical Notation').  We count the actual exported files and
    confirm at least as many as the core languages list (minus slash names).
    """
    site_dir, report, loader = crawled_site
    # Minimum expected: core language records minus those with path-separator
    min_expected = len([
        lang for lang in loader.get_all_languages()
        if "/" not in lang["name"]
    ])
    actual = list((site_dir / "language").glob("*/index.html"))
    assert len(actual) >= min_expected, (
        f"Expected at least {min_expected} language pages, got {len(actual)}"
    )


def test_crawler_links_resolve(crawled_site: tuple) -> None:
    """Every internal href in every emitted file resolves to an existing file."""
    site_dir, _, _ = crawled_site

    href_pattern = re.compile(r'href=["\']([^"\']+)["\']')
    missing: list[str] = []

    for html_file in site_dir.rglob("*.html"):
        content = html_file.read_text(encoding="utf-8")
        for m in href_pattern.finditer(content):
            href = m.group(1)
            # Skip external, anchor, mailto, javascript
            if (
                href.startswith("http")
                or href.startswith("//")
                or href.startswith("#")
                or href.startswith("mailto:")
                or href.startswith("javascript:")
            ):
                continue
            # Resolve relative to the file's directory
            target = (html_file.parent / href).resolve()
            if not target.exists():
                missing.append(f"{html_file.relative_to(site_dir)}: {href}")

    assert not missing, (
        f"{len(missing)} broken internal links found:\n" + "\n".join(missing[:20])
    )


def test_crawler_copies_static_assets(crawled_site: tuple) -> None:
    """site/static/ exists and contains at least one file, or is skipped
    when src/app/static/ is empty."""
    site_dir, _, _ = crawled_site

    this_dir = Path(__file__).parent
    src_static = this_dir.parent / "src" / "app" / "static"

    dst_static = site_dir / "static"
    if any(src_static.rglob("*")):
        assert dst_static.exists(), "site/static/ not created"
        assert any(dst_static.rglob("*")), "site/static/ is empty"
    else:
        pytest.skip("src/app/static/ is empty; nothing to copy")


def test_crawler_no_500s(crawled_site: tuple) -> None:
    """CrawlReport.failures is empty after a full crawl."""
    _, report, _ = crawled_site
    if report.failures:
        details = "\n".join(f"  {f['url']}: {f['error']}" for f in report.failures)
        pytest.fail(f"{report.fail_count} crawl failures:\n{details}")


def test_paradigm_route_renders_foundations_and_languages(
    mock_loader: DataLoader,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ecosystem = _find_representative_paradigm(mock_loader)
    assert ecosystem is not None, "Expected at least one paradigm ecosystem with foundations and languages"

    paradigm_name, paradigm_data = ecosystem
    first_foundation = paradigm_data["foundations"][0]["display_name"]
    first_language = paradigm_data["languages"][0]["display_name"]

    monkeypatch.setattr(app_module, "data_loader", mock_loader)
    monkeypatch.setattr(app_module, "_entity_link_map", None)

    client = TestClient(app_module.app)
    response = client.get(f"/paradigm/{quote(paradigm_name)}")

    assert response.status_code == 200
    assert "Foundational Precursors" in response.text
    assert "Languages in this paradigm" in response.text
    assert first_foundation in response.text
    assert first_language in response.text


def test_crawler_emits_foundation_aware_paradigm_page(crawled_site: tuple) -> None:
    """A crawled paradigm page includes the new foundations section."""
    site_dir, _, loader = crawled_site
    ecosystem = _find_representative_paradigm(loader)
    assert ecosystem is not None, "Expected at least one crawlable paradigm ecosystem with foundations and languages"

    paradigm_name, paradigm_data = ecosystem
    page = site_dir / "paradigm" / quote(paradigm_name, safe="") / "index.html"
    assert page.exists(), f"Expected crawled paradigm page for {paradigm_name}"

    html = page.read_text(encoding="utf-8")
    assert "Foundational Precursors" in html
    assert paradigm_data["foundations"][0]["display_name"] in html
    assert paradigm_data["languages"][0]["display_name"] in html


def test_api_paradigm_ecosystem_route(
    mock_loader: DataLoader,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paradigm_name = "Functional" if "Functional" in mock_loader.get_all_paradigms() else mock_loader.get_all_paradigms()[0]
    monkeypatch.setattr(app_module, "data_loader", mock_loader)
    monkeypatch.setattr(app_module, "_entity_link_map", None)

    client = TestClient(app_module.app)
    response = client.get(f"/api/paradigm/{paradigm_name}/ecosystem")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"paradigm", "languages", "foundations", "stats"}
    assert payload["paradigm"]["name"] == paradigm_name
    assert isinstance(payload["languages"], list)
    assert isinstance(payload["foundations"], list)
    assert payload["stats"]["language_count"] == len(payload["languages"])
    assert payload["stats"]["foundation_count"] == len(payload["foundations"])
