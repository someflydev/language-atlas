import pytest
import os
import json
from pathlib import Path
from app.core.insights import InsightGenerator

@pytest.mark.intensive
def test_insight_generation(db_conn):
    """
    Tests that the InsightGenerator produces valid insights using complex SQL.
    """
    generator = InsightGenerator(db_conn)
    insights = generator.generate_all_insights()
    
    assert "influence_depth" in insights
    assert "paradigm_volatility" in insights
    
    # Check influence depth for a known keystone
    if "ALGOL 60" in insights["influence_depth"]:
        algol_influence = insights["influence_depth"]["ALGOL 60"]
        assert len(algol_influence) > 0
        # First one should be ALGOL 60 itself at depth 0
        assert algol_influence[0]["name"] == "ALGOL 60"
        assert algol_influence[0]["distance"] == 0

    # Check volatility
    volatility = insights["paradigm_volatility"]
    assert len(volatility) > 0
    # Should have ranks
    assert "volatility_rank" in volatility[0]
    assert "decade" in volatility[0]

def test_stamping_engine(db_conn, tmp_path):
    """
    Tests that the stamping engine correctly saves insights to JSON.
    """
    generator = InsightGenerator(db_conn)
    report_path = tmp_path / "historical_insights.json"
    
    generator.stamp_to_json(str(report_path))
    
    assert report_path.exists()
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert "metadata" in data
        assert "influence_depth" in data
        assert "paradigm_volatility" in data
