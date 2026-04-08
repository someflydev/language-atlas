import pytest
import sqlite3
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from app.core.data_loader import DataLoader
from app.core.auditor import AtlasAuditor

@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test_atlas.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE languages (id INTEGER PRIMARY KEY, name TEXT, year INTEGER, cluster TEXT)")
    conn.execute("INSERT INTO languages (name, year, cluster) VALUES ('Python', 1991, 'scripting')")
    
    conn.execute("CREATE TABLE influences (source_id INTEGER, target_id INTEGER)")
    conn.execute("CREATE TABLE paradigms (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE language_paradigms (language_id INTEGER, paradigm_id INTEGER)")
    
    conn.execute("CREATE TABLE language_profiles (id INTEGER PRIMARY KEY, language_id INTEGER, overview TEXT)")
    conn.execute("CREATE TABLE profile_sections (id INTEGER PRIMARY KEY, profile_id INTEGER, section_name TEXT, content TEXT)")
    
    conn.execute("CREATE VIRTUAL TABLE search_index USING fts5(entity_type UNINDEXED, entity_id UNINDEXED, title, content)")
    conn.execute("INSERT INTO search_index (entity_type, entity_id, title) VALUES ('language', 'Python', 'Python')")
    conn.commit()
    conn.close()
    return db_path

class TestDataLoaderHardening:
    def test_sqlite_fallback_safety(self, temp_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify DataLoader handles missing SQLite gracefully."""
        monkeypatch.delenv("USE_SQLITE", raising=False)
        loader = DataLoader(data_dir="non_existent")
        # Should not crash, should just use empty in-memory lists
        assert loader.use_sqlite is False
        assert loader.get_all_languages() == []

    def test_fts_injection_resilience(self, temp_db: Path) -> None:
        """Test resilience against potentially problematic FTS queries."""
        with patch.dict(os.environ, {"USE_SQLITE": "1"}):
            loader = DataLoader()
            loader.db_path = str(temp_db)
            loader.use_sqlite = True
            
            # These should not crash the app even if FTS5 syntax is malformed
            queries = [
                'name MATCH "Python"',
                '"',
                'AND OR NOT',
                '*',
                'name:Python'
            ]
            for q in queries:
                results = loader.search(q)
                assert isinstance(results, list)

    def test_read_only_enforcement(self, temp_db: Path) -> None:
        """Verify that DataLoader connections are indeed read-only."""
        with patch.dict(os.environ, {"USE_SQLITE": "1"}):
            loader = DataLoader()
            loader.db_path = str(temp_db)
            loader.use_sqlite = True
            
            conn = loader._get_connection()
            with pytest.raises(sqlite3.OperationalError):
                conn.execute("INSERT INTO languages (name) VALUES ('HackerLang')")
            conn.close()

class TestAuditorHardening:
    def test_corrupted_json_handling(self, tmp_path: Path) -> None:
        """Test auditor resilience to corrupted JSON files."""
        bad_json = tmp_path / "corrupted.json"
        bad_json.write_text("{ \"name\": \"Python\", broken: }")
        
        auditor = AtlasAuditor(data_path=bad_json)
        success = auditor.validate_json()
        assert success is False
        assert any("Failed to parse JSON" in e for e in auditor.errors)

    def test_missing_required_keys(self, tmp_path: Path) -> None:
        """Test auditor detects missing mandatory schema keys."""
        sparse_json = tmp_path / "sparse.json"
        sparse_json.write_text(json.dumps([{"name": "Python"}])) # Missing almost everything
        
        auditor = AtlasAuditor(data_path=sparse_json)
        success = auditor.validate_json()
        assert success is False
        assert any("missing required key" in e for e in auditor.errors)

class TestFTSIntegrity:
    def test_out_of_sync_fts_detection(self, temp_db: Path) -> None:
        """Verify auditor detects when FTS index is out of sync with main table."""
        conn = sqlite3.connect(temp_db)
        # Add a language but DON'T update FTS
        conn.execute("INSERT INTO languages (name, year, cluster) VALUES ('Rust', 2010, 'systems')")
        conn.commit()
        conn.close()
        
        auditor = AtlasAuditor(db_path=temp_db)
        success = auditor.validate_sqlite()
        assert success is False
        assert any("out of sync" in e for e in auditor.errors)
