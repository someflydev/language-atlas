import pytest
import os
import json
import sqlite3
from pathlib import Path
from pytest import MonkeyPatch
from app.core.data_loader import DataLoader

def test_dataloader_json_all_methods(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Exhaustively test all DataLoader methods using JSON backend."""
    monkeypatch.setenv("USE_SQLITE", "0")
    
    # Setup mock data directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "languages.json").write_text(json.dumps([{"name": "Python", "year": 1991, "cluster": "scripting", "paradigms": ["Object-Oriented"]}]))
    (data_dir / "paradigms.json").write_text(json.dumps([{"name": "Object-Oriented", "description": "OO description", "year_introduced": 1967, "motivation": "Crisis", "languages": ["Python"], "connected_paradigms": ["Procedural"], "key_features": {"The Reaction": "reaction"}}]))
    (data_dir / "eras.json").write_text(json.dumps([{
        "name": "Early Era", 
        "slug": "early",
        "year_start": 1950,
        "description": "Early Era",
        "crossroads": [{"title": "CR1", "explanation": "expl"}],
        "modern_reactions": [{"theme": "R1", "explanation": "expl"}],
        "timeline_events": [{"year": "1950", "description": "event1"}]
    }]))
    (data_dir / "concepts.json").write_text(json.dumps([{"name": "Garbage Collection"}]))
    (data_dir / "influences.json").write_text(json.dumps([{"from": "ABC", "to": "Python"}]))
    (data_dir / "people.json").write_text(json.dumps([{"name": "Guido van Rossum"}]))
    (data_dir / "learning_paths.json").write_text(json.dumps([{"id": "path1", "title": "Path 1", "steps": []}]))
    
    docs_dir = data_dir / "docs"
    (docs_dir / "language_profiles").mkdir(parents=True)
    (docs_dir / "concept_profiles").mkdir(parents=True)
    (docs_dir / "people_profiles").mkdir(parents=True)
    (docs_dir / "historical_events").mkdir(parents=True)
    (docs_dir / "org_profiles").mkdir(parents=True)
    (docs_dir / "era_summaries").mkdir(parents=True)
    
    (docs_dir / "language_profiles" / "Python.json").write_text(json.dumps({"title": "Python Profile"}))
    (docs_dir / "concept_profiles" / "Garbage_Collection.json").write_text(json.dumps({"title": "GC Profile"}))
    (docs_dir / "people_profiles" / "Guido_van_Rossum.json").write_text(json.dumps({"title": "Guido Profile"}))
    (docs_dir / "historical_events" / "event1.json").write_text(json.dumps({"title": "Event 1", "slug": "event1"}))
    (docs_dir / "org_profiles" / "PSF.json").write_text(json.dumps({"title": "PSF Profile"}))
    (docs_dir / "era_summaries" / "early.json").write_text(json.dumps({"slug": "early", "title": "Early Era"}))


    loader = DataLoader(data_dir=str(data_dir))
    
    # Test all the getters
    language = loader.get_language("Python")
    assert language is not None
    assert language["name"] == "Python"
    language_profile = loader.get_language_profile("Python")
    assert language_profile is not None
    assert language_profile["title"] == "Python Profile"
    combined = loader.get_combined_language_data("Python")
    assert combined is not None
    assert combined["title"] == "Python Profile"
    concept_profile = loader.get_concept_profile("Garbage Collection")
    assert concept_profile is not None
    assert concept_profile["title"] == "GC Profile"
    person = loader.get_person("Guido van Rossum")
    assert person is not None
    assert person["title"] == "Guido Profile"
    event = loader.get_event("event1")
    assert event is not None
    assert event["title"] == "Event 1"
    org = loader.get_org("PSF")
    assert org is not None
    assert org["title"] == "PSF Profile"
    assert len(loader.get_all_era_summaries()) == 1
    era_summary = loader.get_era_summary("early")
    assert era_summary is not None
    assert era_summary["title"] == "Early Era"
    assert len(loader.get_crossroads()) == 1
    assert len(loader.get_modern_reactions()) == 1
    assert len(loader.get_timeline()) == 1
    assert len(loader.get_all_languages()) == 1
    assert "scripting" in loader.get_all_clusters()
    assert "Object-Oriented" in loader.get_all_paradigms()
    assert loader.get_paradigm_info("Object-Oriented")["name"] == "Object-Oriented"
    assert loader.get_cluster_info("scripting")["name"] == "scripting"
    assert len(loader.get_timeline_data()) == 1
    assert len(loader.get_influence_data()) == 0 # ABC not in languages
    learning_path = loader.get_learning_path("path1")
    assert learning_path is not None
    assert learning_path["title"] == "Path 1"
    auto_odyssey = loader.get_auto_odyssey("Python")
    assert auto_odyssey is not None
    assert auto_odyssey["id"] == "auto_python"

def test_dataloader_sqlite_extended_methods(mock_loader: DataLoader) -> None:
    """Test the SQLite paths for all getter methods to ensure full coverage."""
    # 1. Core Lookups
    python_lang = mock_loader.get_language("Python")
    assert python_lang is not None
    assert python_lang["name"] == "Python"
    assert mock_loader.get_language("None") is None
    
    # 2. Profiles
    profiles = mock_loader.get_language_profiles()
    assert isinstance(profiles, dict)
    
    profile = mock_loader.get_language_profile("Python")
    assert profile is not None
    assert "id" in profile
    
    # 3. Concepts
    concepts = mock_loader.get_all_concepts()
    assert len(concepts) > 0
    
    c_profile = mock_loader.get_concept_profile("The Actor Model")
    if c_profile:
        assert "title" in c_profile
        
    # 4. People
    people = mock_loader.get_all_people()
    assert len(people) > 0
    
    p_profiles = mock_loader.get_people_profiles()
    assert isinstance(p_profiles, dict)
    
    person = mock_loader.get_person("Guido van Rossum")
    if person:
        assert "name" in person
        
    # 5. Organizations
    org_profiles = mock_loader.get_org_profiles()
    assert isinstance(org_profiles, dict)
    
    org = mock_loader.get_org("Bell Labs")
    if org:
        assert "name" in org
        
    # 6. Events
    events = mock_loader.get_historical_events()
    assert isinstance(events, dict)
    
    event = mock_loader.get_event("birth_of_the_web")
    if event:
        assert "title" in event
        
    # 7. Eras & Narrative
    eras = mock_loader.get_all_era_summaries()
    assert len(eras) > 0
    
    era = mock_loader.get_era_summary("SYSTEMS_RENAISSANCE")
    if era:
        assert "id" in era
        assert "key_drivers" in era
        assert "pivotal_languages" in era
        
    crossroads = mock_loader.get_crossroads()
    assert len(crossroads) > 0
    
    reactions = mock_loader.get_modern_reactions()
    assert len(reactions) > 0
    
    timeline = mock_loader.get_timeline()
    assert len(timeline) > 0
    
    # 8. Lists & Aggregates
    assert len(mock_loader.get_all_clusters()) > 0
    assert len(mock_loader.get_all_paradigms()) > 0
    assert len(mock_loader.get_all_influences()) > 0
    
    # 9. Search & Utils
    results = mock_loader.search("Python")
    assert isinstance(results, list)
    
    link_map = mock_loader.get_entity_link_map()
    assert "Python" in link_map
    
    # 10. Complex Filtered Language List
    langs = mock_loader.get_all_languages(
        clusters=["scripting"], 
        paradigms=["Object-Oriented"],
        min_year=1990,
        max_year=2000,
        sort="name"
    )
    assert isinstance(langs, list)
    
    # 11. Influence & Odysseys
    infl = mock_loader.get_influences("Python")
    assert infl is not None
    assert "influenced_by" in infl
    
    paths = mock_loader.get_learning_paths()
    assert len(paths) > 0
    
    path = mock_loader.get_learning_path("intro_path")
    if path:
        assert "steps" in path
        
    auto = mock_loader.get_auto_odyssey("C")
    assert auto is not None
    
    # 12. Comparison
    comp = mock_loader.get_comparison_data(["Python", "Rust"])
    assert len(comp) >= 1

def test_dataloader_edge_cases(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test edge cases like missing files and empty directories."""
    monkeypatch.setenv("USE_SQLITE", "0")
    data_dir = tmp_path / "empty_data"
    data_dir.mkdir()
    
    loader = DataLoader(data_dir=str(data_dir))
    assert loader.get_all_languages() == []
    assert loader.get_language("None") is None
    assert loader.get_language_profile("None") is None
    assert loader.get_event("None") is None
    assert loader.get_org("None") is None
    assert loader.get_person("None") is None


def test_new_site_builder_dataloader_methods(mock_loader: DataLoader) -> None:
    """One-line smoke tests for methods added to support SiteBuilder."""
    assert mock_loader.get_language_doc_info("Python") is not None
    first_concept = mock_loader.get_all_concepts()[0]["name"]
    assert mock_loader.get_concept_doc_info(first_concept) is not None
    assert isinstance(mock_loader.get_all_paradigm_objects(), list)
    assert isinstance(mock_loader.get_paradigm_matrix(), list)
    assert isinstance(mock_loader.get_timeline_with_related(), list)
    assert len(mock_loader.get_top_influential(5)) <= 5
    assert "languages" in mock_loader.get_entity_counts()
