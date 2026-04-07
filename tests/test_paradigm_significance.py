import pytest
import json
from app.core.data_loader import DataLoader

def test_get_primary_paradigm_json(tmp_path, monkeypatch):
    monkeypatch.setenv("USE_SQLITE", "0")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    (data_dir / "languages.json").write_text(json.dumps([
        {"name": "Scala", "paradigms": ["Object-Oriented", "Functional", "Concurrent"]},
        {"name": "C", "paradigms": ["Procedural", "Imperative"]},
        {"name": "Missing", "paradigms": []}
    ]))
    
    loader = DataLoader(data_dir=str(data_dir))
    
    assert loader.get_primary_paradigm("Scala") == "Object-Oriented"
    assert loader.get_primary_paradigm("C") == "Procedural"
    assert loader.get_primary_paradigm("Missing") is None
    assert loader.get_primary_paradigm("Unknown") is None

def test_get_all_languages_weighting_json(tmp_path, monkeypatch):
    monkeypatch.setenv("USE_SQLITE", "0")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    (data_dir / "languages.json").write_text(json.dumps([
        {"name": "Scala", "paradigms": ["Object-Oriented", "Functional", "Concurrent"], "year": 2004},
        {"name": "Java", "paradigms": ["Object-Oriented", "Imperative"], "year": 1995},
        {"name": "Haskell", "paradigms": ["Functional"], "year": 1990},
        {"name": "Erlang", "paradigms": ["Actor-model", "Functional", "Concurrent"], "year": 1986}
    ]))
    
    loader = DataLoader(data_dir=str(data_dir))
    
    # Unweighted, sort by year
    langs_unweighted = loader.get_all_languages(paradigms=["Functional"], sort="year")
    # 1986 (Erlang), 1990 (Haskell), 2004 (Scala)
    assert [l["name"] for l in langs_unweighted] == ["Erlang", "Haskell", "Scala"]
    
    # Weighted, primary Functional comes first (Haskell)
    langs_weighted = loader.get_all_languages(paradigms=["Functional"], sort="year", primary_paradigm_weighting=True)
    assert [l["name"] for l in langs_weighted] == ["Haskell", "Erlang", "Scala"]

def test_get_primary_paradigm_sqlite(mock_loader):
    scala_primary = mock_loader.get_primary_paradigm("Scala")
    assert scala_primary is not None
    assert isinstance(scala_primary, str)

def test_get_all_languages_weighting_sqlite(mock_loader):
    langs_weighted = mock_loader.get_all_languages(paradigms=["Functional"], primary_paradigm_weighting=True)
    langs_unweighted = mock_loader.get_all_languages(paradigms=["Functional"], primary_paradigm_weighting=False)
    
    assert len(langs_weighted) == len(langs_unweighted)
    
    # First item in weighted should have 'Functional' as primary
    assert langs_weighted[0]['paradigms'][0] == "Functional"
