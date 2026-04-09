"""Tests for SiteCrawler in src/app/core/site_builder.py.

Requires language_atlas.sqlite to exist (run `make build` if absent).
The crawl runs once per test session via a session-scoped fixture.
"""

import os
import re
from pathlib import Path

import pytest

from app.core.data_loader import DataLoader
from app.core.site_builder import CrawlReport, SiteCrawler


def _make_loader() -> DataLoader:
    os.environ.setdefault("USE_SQLITE", "1")
    return DataLoader()


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
