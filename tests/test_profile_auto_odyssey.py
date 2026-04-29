import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app import app as app_module
from app.core.data_loader import DataLoader
from app.core.site_builder import SiteCrawler


def _write_auto_odyssey_fixture(
    generated_dir: Path,
    candidate: dict[str, Any],
) -> None:
    path = generated_dir / "odyssey" / "auto-odyssey-candidates.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"generated_at": "test", "count": 1, "candidates": [candidate]}),
        encoding="utf-8",
    )


def _patch_app(
    monkeypatch: Any,
    mock_loader: DataLoader,
    generated_dir: Path,
) -> None:
    monkeypatch.setattr(app_module, "data_loader", mock_loader)
    monkeypatch.setattr(app_module, "GENERATED_DATA_DIR", str(generated_dir))
    monkeypatch.setattr(app_module, "_entity_link_map", None)
    monkeypatch.setattr(app_module, "_graph_reports_dir", None)
    monkeypatch.setattr(app_module, "_auto_odyssey_dir", None)
    monkeypatch.setattr(app_module, "_auto_odyssey_candidates", {})


def test_language_profile_uses_generated_auto_odyssey_without_dynamic_call(
    tmp_path: Path,
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    _write_auto_odyssey_fixture(
        tmp_path,
        {
            "name": "Python",
            "display_name": "Python",
            "steps": [
                {
                    "language": "TypeScript",
                    "display_name": "Typed JavaScript",
                    "milestone": "Generation 1 Impact",
                }
            ],
        },
    )

    def fail_dynamic_call(_name: str) -> None:
        raise AssertionError("profile route must not call get_auto_odyssey")

    monkeypatch.setattr(mock_loader, "get_auto_odyssey", fail_dynamic_call)
    _patch_app(monkeypatch, mock_loader, tmp_path)

    response = TestClient(app_module.app).get("/language/Python")

    assert response.status_code == 200
    assert "Dynamic Heritage Journey" in response.text
    assert "Typed JavaScript" in response.text
    assert 'href="/language/TypeScript"' in response.text


def test_language_profile_omits_auto_odyssey_when_artifact_absent(
    tmp_path: Path,
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    _patch_app(monkeypatch, mock_loader, tmp_path)

    response = TestClient(app_module.app).get("/language/Python")

    assert response.status_code == 200
    assert "Dynamic Heritage Journey" not in response.text


def test_language_profile_omits_auto_odyssey_when_steps_unusable(
    tmp_path: Path,
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    _write_auto_odyssey_fixture(
        tmp_path,
        {
            "name": "Python",
            "display_name": "Python",
            "direct_descendant_count": 4,
            "total_descendant_count": 12,
        },
    )
    _patch_app(monkeypatch, mock_loader, tmp_path)

    response = TestClient(app_module.app).get("/language/Python")

    assert response.status_code == 200
    assert "Dynamic Heritage Journey" not in response.text


def test_language_profile_omits_auto_odyssey_when_artifact_malformed(
    tmp_path: Path,
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    path = tmp_path / "odyssey" / "auto-odyssey-candidates.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not-json", encoding="utf-8")
    _patch_app(monkeypatch, mock_loader, tmp_path)

    response = TestClient(app_module.app).get("/language/Python")

    assert response.status_code == 200
    assert "Dynamic Heritage Journey" not in response.text


def test_site_crawler_bakes_generated_auto_odyssey_into_profile_html(
    tmp_path: Path,
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    generated_dir = tmp_path / "generated"
    site_dir = tmp_path / "site"
    _write_auto_odyssey_fixture(
        generated_dir,
        {
            "name": "Python",
            "display_name": "Python",
            "steps": [
                {
                    "language": "TypeScript",
                    "display_name": "Typed JavaScript",
                    "milestone": "Generation 1 Impact",
                }
            ],
        },
    )
    _patch_app(monkeypatch, mock_loader, generated_dir)

    crawler = SiteCrawler(mock_loader, site_dir)
    monkeypatch.setattr(
        crawler,
        "_enumerate_urls",
        lambda: ["/language/Python", "/language/TypeScript"],
    )

    report = crawler.crawl()
    page = site_dir / "language" / "Python" / "index.html"

    assert not report.failures
    assert page.is_file()
    html = page.read_text(encoding="utf-8")
    assert "Dynamic Heritage Journey" in html
    assert "Typed JavaScript" in html
    assert "language/TypeScript/index.html" in html
