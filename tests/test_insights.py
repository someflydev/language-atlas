import pytest
import os
import json
from pathlib import Path
from app.core.insights import InsightGenerator, AtlasAnalytics

class NoCloseConnection:
    """Wrapper for sqlite3.Connection that ignores close() calls."""
    def __init__(self, conn): self._conn = conn
    def __getattr__(self, name): return getattr(self._conn, name)
    def close(self): pass

@pytest.mark.intensive
def test_insight_generation(db_conn):
    """
    Tests that the InsightGenerator produces valid insights using complex SQL.
    """
    safe_conn = NoCloseConnection(db_conn)
    generator = InsightGenerator(safe_conn)
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
    safe_conn = NoCloseConnection(db_conn)
    generator = InsightGenerator(safe_conn)
    report_path = tmp_path / "historical_insights.json"
    
    generator.stamp_to_json(str(report_path))
    
    assert report_path.exists()
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert "metadata" in data
        assert "influence_depth" in data
        assert "paradigm_volatility" in data

def test_atlas_analytics(db_conn):
    """Tests all methods of the AtlasAnalytics class."""
    safe_conn = NoCloseConnection(db_conn)
    analytics = AtlasAnalytics(safe_conn)
    
    # 1. Safety & Complexity Trends
    trends = analytics.generate_safety_complexity_trends()
    assert isinstance(trends, dict)
    if trends:
        decade = list(trends.keys())[0]
        assert "avg_complexity" in trends[decade]
        assert "safety_distribution" in trends[decade]
        
    # 2. Creator Impact
    impact = analytics.generate_creator_impact()
    assert isinstance(impact, list)
    if impact:
        assert "total_impact" in impact[0]
        assert "name" in impact[0]
        
    # 3. Cluster Genealogy
    genealogy = analytics.generate_cluster_genealogy()
    assert isinstance(genealogy, dict)
    if genealogy:
        cluster = list(genealogy.keys())[0]
        assert "internal" in genealogy[cluster]
        assert "external" in genealogy[cluster]
        assert "ratio" in genealogy[cluster]
        
    # 4. Innovation Trends
    innovations = analytics.generate_innovation_trends()
    assert isinstance(innovations, dict)
    
    # 5. DB Health
    health = analytics.generate_db_health()
    assert "orphans" in health
    assert "terminal" in health
    assert "summary" in health
    assert "orphan_count" in health["summary"]
