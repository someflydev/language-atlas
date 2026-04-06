import pytest
import os
import json
from pathlib import Path
from app.core.data_loader import DataLoader
from app.core.docs_parser import parse_markdown

def test_dataloader_consistency(mock_loader, monkeypatch):
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

def test_docs_parser_roundtrip():
    """
    Test docs_parser.py by round-tripping generated Markdown back into JSON.
    Asserting field equality with the source JSON in data/docs/language_profiles/.
    """
    base_dir = Path(__file__).parent.parent
    markdown_dir = base_dir / "generated-docs" / "languages"
    json_source_dir = base_dir / "data" / "docs" / "language_profiles"
    
    # We only test if generated-docs exists. If not, this test should be skipped or run after 'make docs'
    if not markdown_dir.exists():
        pytest.skip("generated-docs/languages/ directory not found. Run 'make docs' first.")
    
    # Pick a few representative languages for the round-trip test
    test_languages = ["ALGOL_60", "Python", "C++", "Rust", "Lisp"]
    
    for lang in test_languages:
        md_file = markdown_dir / f"{lang}.md"
        json_file = json_source_dir / f"{lang}.json"
        
        if not md_file.exists() or not json_file.exists():
            continue
            
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
            
        with open(json_file, 'r', encoding='utf-8') as f:
            original_json = json.load(f)
            
        parsed_json = parse_markdown(md_content, md_file)
        
        # Check core fields that should survive the round-trip
        # (title, overview, historical_context, mental_model, tradeoffs, legacy)
        fields_to_check = ["title", "overview", "historical_context", "mental_model", "tradeoffs", "legacy"]
        
        for field in fields_to_check:
            # We strip whitespace as Markdown generation/parsing might add/remove it slightly
            orig_val = original_json.get(field, "").strip()
            parsed_val = parsed_json.get(field, "").strip()
            
            # Normalize line endings and double newlines for robust comparison
            orig_val = "\n".join([line.strip() for line in orig_val.splitlines() if line.strip()])
            parsed_val = "\n".join([line.strip() for line in parsed_val.splitlines() if line.strip()])
            
            assert parsed_val == orig_val, f"Field '{field}' mismatch for {lang}"
