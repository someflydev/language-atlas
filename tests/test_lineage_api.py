import json
from pathlib import Path
from typing import Any

import sqlite3
from fastapi.testclient import TestClient
from fastapi.responses import HTMLResponse

from app import app as app_module
from app.core.data_loader import DataLoader


def _client_with_loader(monkeypatch: Any, loader: DataLoader) -> TestClient:
    monkeypatch.setattr(app_module, "data_loader", loader)
    return TestClient(app_module.app)


def test_api_lineage_known_language(mock_loader: DataLoader, monkeypatch: Any) -> None:
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get("/api/lineage/Python")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Python"
    assert data["ancestors"]
    assert data["descendants"]
    assert data["ancestor_count"] == len(data["ancestors"])
    assert data["descendant_count"] == len(data["descendants"])
    assert {"name", "display_name", "entity_type", "year", "depth", "path_count"} <= set(
        data["ancestors"][0]
    )


def test_api_lineage_unknown_language(mock_loader: DataLoader, monkeypatch: Any) -> None:
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get("/api/lineage/DefinitelyUnknownLanguage")

    assert response.status_code == 404
    assert response.json() == {"error": "Language not found"}


def test_api_lineage_language_without_connections(monkeypatch: Any) -> None:
    class EmptyLineageLoader:
        def get_lineage(self, name: str) -> dict[str, Any]:
            return {
                "name": name,
                "display_name": name,
                "entity_type": "language",
                "year": 2024,
                "ancestor_count": 0,
                "descendant_count": 0,
                "max_ancestor_depth": 0,
                "max_descendant_depth": 0,
                "ancestors": [],
                "descendants": [],
            }

    monkeypatch.setattr(app_module, "data_loader", EmptyLineageLoader())
    client = TestClient(app_module.app)

    response = client.get("/api/lineage/Isolate")

    assert response.status_code == 200
    data = response.json()
    assert data["ancestors"] == []
    assert data["descendants"] == []


def test_api_path_reachable(
    db_conn: sqlite3.Connection,
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    pair = db_conn.execute(
        """
        SELECT f.name AS from_name, t.name AS to_name
        FROM language_reachability r
        JOIN languages f ON f.id = r.from_language_id
        JOIN languages t ON t.id = r.to_language_id
        ORDER BY r.min_depth ASC, f.name ASC, t.name ASC
        LIMIT 1
        """
    ).fetchone()
    assert pair is not None
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get(
        "/api/path",
        params={"from": pair["from_name"], "to": pair["to_name"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reachable"] is True
    assert data["min_depth"] >= 1
    assert data["path_count"] >= 1
    assert isinstance(data["sample_paths"], list)


def test_api_path_not_reachable(
    db_conn: sqlite3.Connection,
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    pair = db_conn.execute(
        """
        SELECT f.name AS from_name, t.name AS to_name
        FROM languages f
        CROSS JOIN languages t
        LEFT JOIN language_reachability r
          ON r.from_language_id = f.id
         AND r.to_language_id = t.id
        WHERE f.id != t.id
          AND r.from_language_id IS NULL
        ORDER BY f.name ASC, t.name ASC
        LIMIT 1
        """
    ).fetchone()
    assert pair is not None
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get(
        "/api/path",
        params={"from": pair["from_name"], "to": pair["to_name"]},
    )

    assert response.status_code == 200
    assert response.json()["reachable"] is False
    assert response.json()["min_depth"] is None


def test_api_path_same_language_returns_400(
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get("/api/path", params={"from": "Python", "to": "Python"})

    assert response.status_code == 400
    assert response.json() == {"error": "Source and target languages must be different"}


def test_api_path_unknown_language_returns_404(
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get("/api/path", params={"from": "UNKNOWN", "to": "Python"})

    assert response.status_code == 404
    assert response.json() == {"error": "Source language not found"}


def test_path_page_empty_state(mock_loader: DataLoader, monkeypatch: Any) -> None:
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get("/path")

    assert response.status_code == 200
    assert "Origin Language" in response.text
    assert "Destination Language" in response.text


def test_path_page_reachable_renders_path_chain(
    db_conn: sqlite3.Connection,
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    path = db_conn.execute(
        """
        SELECT f.name AS from_name, t.name AS to_name, p.path_text
        FROM language_lineage_paths_bounded p
        JOIN languages f ON f.id = p.from_language_id
        JOIN languages t ON t.id = p.to_language_id
        ORDER BY p.depth ASC, f.name ASC, t.name ASC
        LIMIT 1
        """
    ).fetchone()
    assert path is not None
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get(
        "/path",
        params={"from": path["from_name"], "to": path["to_name"]},
    )

    assert response.status_code == 200
    assert path["path_text"].split(" -> ")[0] in response.text
    assert "&rarr;" in response.text


def test_path_page_not_reachable_renders_message(
    db_conn: sqlite3.Connection,
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    pair = db_conn.execute(
        """
        SELECT f.name AS from_name, t.name AS to_name
        FROM languages f
        CROSS JOIN languages t
        LEFT JOIN language_reachability r
          ON r.from_language_id = f.id
         AND r.to_language_id = t.id
        WHERE f.id != t.id
          AND r.from_language_id IS NULL
        ORDER BY f.name ASC, t.name ASC
        LIMIT 1
        """
    ).fetchone()
    assert pair is not None
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get(
        "/path",
        params={"from": pair["from_name"], "to": pair["to_name"]},
    )

    assert response.status_code == 200
    assert "No influence path found" in response.text


def test_path_page_unknown_origin_renders_error(
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get("/path", params={"from": "UNKNOWN", "to": "Python"})

    assert response.status_code == 200
    assert "Origin language not found" in response.text


def test_dataloader_get_cousins_returns_shared_ancestor_matches(
    mock_loader: DataLoader,
) -> None:
    cousins: list[dict[str, Any]] = []
    for language in mock_loader.get_all_languages(entity_type=None):
        cousins = mock_loader.get_cousins(language["name"])
        if cousins:
            break

    assert cousins, "Expected at least one cousin language relationship"
    assert all(item["shared_ancestor_count"] >= 2 for item in cousins)
    assert {"name", "display_name", "entity_type", "year", "influence_score", "shared_ancestor_count"} <= set(cousins[0])


def test_dataloader_get_cousins_no_ancestors_returns_empty(
    mock_loader: DataLoader,
) -> None:
    assert mock_loader.get_cousins("COMIT") == []


def test_profile_route_context_includes_cousins_key(
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    captured: dict[str, Any] = {}

    def fake_template_response(*args: Any, **kwargs: Any) -> HTMLResponse:
        captured.update(kwargs.get("context", {}))
        return HTMLResponse("ok")

    monkeypatch.setattr(app_module, "data_loader", mock_loader)
    monkeypatch.setattr(app_module, "auto_link_content", lambda html: html)
    monkeypatch.setattr(app_module.templates, "TemplateResponse", fake_template_response)

    client = TestClient(app_module.app)
    response = client.get("/language/Python")

    assert response.status_code == 200
    assert "cousins" in captured


def test_dataloader_lineage_methods_gracefully_degrade_in_json_mode(
    monkeypatch: Any,
) -> None:
    loader = DataLoader()
    monkeypatch.setattr(loader, "use_sqlite", False)
    monkeypatch.setattr(
        loader,
        "languages",
        [
            {"name": "Source", "display_name": "Source"},
            {"name": "Target", "display_name": "Target"},
        ],
    )

    assert loader.get_lineage("Source") is None
    assert loader.get_cousins("Source") == []
    assert loader.get_path("Source", "Target") == {
        "from": "Source",
        "to": "Target",
        "reachable": False,
        "min_depth": None,
        "path_count": 0,
        "sample_paths": [],
    }


def test_dataloader_lineage_items_include_influence_score(
    mock_loader: DataLoader,
) -> None:
    lineage = mock_loader.get_lineage("Python")

    assert lineage is not None
    assert lineage["ancestors"]
    assert "influence_score" in lineage["ancestors"][0]
    if lineage["descendants"]:
        assert "influence_score" in lineage["descendants"][0]


def test_report_endpoints_return_503_when_file_absent(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(app_module, "GENERATED_DATA_DIR", str(tmp_path))
    client = TestClient(app_module.app)

    for route in (
        "/api/reports/keystones",
        "/api/reports/bridges",
        "/api/reports/orphans",
        "/api/viz/influence-expanded",
    ):
        response = client.get(route)
        assert response.status_code == 503
        assert "make derived-data" in response.json()["error"]


def test_report_endpoints_return_generated_json(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    files = {
        "reports/keystone-entities.json": {"items": [{"name": "LISP"}]},
        "reports/bridge-entities.json": {"items": [{"name": "ALGOL 60"}]},
        "reports/orphan-subgraphs.json": {"components": []},
        "viz/influence-expanded.json": {"nodes": [], "edges": []},
    }
    for relative_path, payload in files.items():
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(app_module, "GENERATED_DATA_DIR", str(tmp_path))
    client = TestClient(app_module.app)

    expected = {
        "/api/reports/keystones": files["reports/keystone-entities.json"],
        "/api/reports/bridges": files["reports/bridge-entities.json"],
        "/api/reports/orphans": files["reports/orphan-subgraphs.json"],
        "/api/viz/influence-expanded": files["viz/influence-expanded.json"],
    }
    for route, payload in expected.items():
        response = client.get(route)
        assert response.status_code == 200
        assert response.json() == payload
