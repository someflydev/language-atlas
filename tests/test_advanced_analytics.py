import sqlite3
from typing import Any

from fastapi.testclient import TestClient
from typer.testing import CliRunner

import cli as atlas_cli
from app import app as app_module
from app.core.data_loader import DataLoader
from app.core.insights import InsightGenerator


runner = CliRunner()


def _client_with_loader(monkeypatch: Any, loader: DataLoader) -> TestClient:
    monkeypatch.setattr(app_module, "data_loader", loader)
    return TestClient(app_module.app)


def test_leverage_scores_shape_and_limit(db_conn: sqlite3.Connection) -> None:
    generator = InsightGenerator(db_conn)

    results = generator.calculate_leverage_scores(limit=5)

    assert len(results) <= 5
    assert results
    required = {
        "name",
        "display_name",
        "entity_type",
        "year",
        "leverage_score",
        "descendant_count",
        "max_ancestor_depth",
    }
    for row in results:
        assert required <= set(row)
        assert row["leverage_score"] > 0


def test_leverage_score_formula_for_known_language(db_conn: sqlite3.Connection) -> None:
    generator = InsightGenerator(db_conn)

    results = generator.calculate_leverage_scores(limit=200)
    assembly = next(row for row in results if row["name"] == "Assembly")

    descendant_count = db_conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM language_descendants ld
        JOIN languages l ON l.id = ld.root_language_id
        WHERE l.name = 'Assembly'
        """
    ).fetchone()["count"]
    max_ancestor_depth = db_conn.execute(
        """
        SELECT MAX(depth) AS depth
        FROM language_ancestry la
        JOIN languages l ON l.id = la.root_language_id
        WHERE l.name = 'Assembly'
        """
    ).fetchone()["depth"]
    expected = round(descendant_count / max(max_ancestor_depth or 0, 1), 2)

    assert assembly["descendant_count"] == descendant_count
    assert assembly["max_ancestor_depth"] == max_ancestor_depth
    assert assembly["leverage_score"] == expected


def test_concept_diffusion_contract(db_conn: sqlite3.Connection) -> None:
    generator = InsightGenerator(db_conn)

    results = generator.calculate_concept_diffusion()

    assert results
    for row in results:
        assert row["diffusion_score"] >= row["direct_languages"]
        assert {
            "paradigm_name",
            "direct_languages",
            "diffusion_score",
            "primary_carrier_name",
            "primary_carrier_year",
        } <= set(row)


def test_detect_graph_anomalies_contract(db_conn: sqlite3.Connection) -> None:
    generator = InsightGenerator(db_conn)

    result = generator.detect_graph_anomalies()

    assert set(result) == {"deep_chains", "outliers", "era_gaps"}
    assert isinstance(result["deep_chains"], list)
    assert isinstance(result["outliers"], list)
    assert isinstance(result["era_gaps"], list)


def test_advanced_analytics_api_routes(mock_loader: DataLoader, monkeypatch: Any) -> None:
    client = _client_with_loader(monkeypatch, mock_loader)

    leverage_response = client.get("/api/insights/leverage")
    assert leverage_response.status_code == 200
    assert leverage_response.json()

    diffusion_response = client.get("/api/insights/concept-diffusion")
    assert diffusion_response.status_code == 200
    assert diffusion_response.json()

    anomalies_response = client.get("/api/insights/anomalies")
    assert anomalies_response.status_code == 200
    assert set(anomalies_response.json()) == {"deep_chains", "outliers", "era_gaps"}


def test_insights_page_renders_advanced_sections(
    mock_loader: DataLoader,
    monkeypatch: Any,
) -> None:
    client = _client_with_loader(monkeypatch, mock_loader)

    response = client.get("/insights")

    assert response.status_code == 200
    assert "Leverage" in response.text
    assert "Diffusion" in response.text


def test_cli_leverage_runs(mock_loader: DataLoader, monkeypatch: Any) -> None:
    monkeypatch.setattr(atlas_cli, "get_loader", lambda: mock_loader)

    result = runner.invoke(atlas_cli.app, ["leverage", "--limit", "5"])

    assert result.exit_code == 0
    assert "Rank" in result.stdout
    assert "Leverage" in result.stdout


def test_cli_anomalies_runs(mock_loader: DataLoader, monkeypatch: Any) -> None:
    monkeypatch.setattr(atlas_cli, "get_loader", lambda: mock_loader)

    result = runner.invoke(atlas_cli.app, ["anomalies"])

    assert result.exit_code == 0
