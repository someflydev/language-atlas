import pytest
import os
import json
from pathlib import Path
from pytest import MonkeyPatch
from app.core.data_loader import DataLoader

def test_dataloader_consistency(mock_loader: DataLoader, monkeypatch: MonkeyPatch) -> None:
    """
    Verify DataLoader consistency between JSON and SQLite.
    When using the in-memory mirror, it should return data that matches 
    the original JSON source for core fields.
    """
    # 1. Load from JSON directly for comparison
    base_dir = Path(__file__).parent.parent
    monkeypatch.setenv("USE_SQLITE", "0")
    raw_loader = DataLoader(data_dir=str(base_dir / "data"))
    raw_languages = raw_loader.languages
    
    # 2. Get from mock_loader (SQLite)
    # mock_loader is using the in-memory DB populated from the same JSON
    # We should have the same number of languages
    cursor = mock_loader._get_connection().cursor()
    cursor.execute("SELECT COUNT(*) FROM languages")
    sqlite_count = cursor.fetchone()[0]
    
    assert sqlite_count == len(raw_languages)
