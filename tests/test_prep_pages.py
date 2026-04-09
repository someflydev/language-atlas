"""Acceptance tests for scripts/prep_pages.py.

Tests verify:
1. The script refuses to run when the current branch is main.
2. The script writes index.html and .nojekyll under the repo root.
3. The script copies the database into site/db/atlas/ and writes a
   valid config.json.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


def _load_prep_pages():
    """Load scripts/prep_pages.py as a module (not via sys.path import)."""
    spec = importlib.util.spec_from_file_location(
        "prep_pages", _SCRIPTS_DIR / "prep_pages.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_db(path: Path, size: int = 4096) -> None:
    """Write a minimal fake SQLite file (correct magic bytes + padding)."""
    # SQLite files start with "SQLite format 3\000" (16 bytes).
    header = b"SQLite format 3\x00"
    path.write_bytes(header + b"\x00" * (size - len(header)))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_prep_pages_refuses_on_main(monkeypatch, tmp_path, capsys):
    """main() must exit non-zero with a 'Refusing' message when on main."""
    mod = _load_prep_pages()
    monkeypatch.setattr(mod, "_current_branch", lambda: "main")
    monkeypatch.chdir(tmp_path)

    result = mod.main()

    assert result != 0
    captured = capsys.readouterr()
    assert "Refusing" in captured.err


def test_prep_pages_writes_redirect_html(monkeypatch, tmp_path):
    """main() must write index.html and .nojekyll at the repo root."""
    mod = _load_prep_pages()
    monkeypatch.setattr(mod, "_current_branch", lambda: "gh-pages")
    monkeypatch.chdir(tmp_path)

    # Provide the minimum inputs the script expects.
    _make_fake_db(tmp_path / "language_atlas.sqlite")
    (tmp_path / "site").mkdir()

    result = mod.main()

    assert result == 0, "main() should succeed"
    assert (tmp_path / "index.html").exists(), "index.html must be created"
    assert (tmp_path / ".nojekyll").exists(), ".nojekyll must be created"

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'meta http-equiv="refresh"' in html, (
        "index.html must contain a meta-refresh redirect"
    )
    assert "site/" in html, "redirect target must point at site/"


def test_prep_pages_chunks_database(monkeypatch, tmp_path):
    """main() must copy the database into site/db/atlas/ with a valid config.json."""
    mod = _load_prep_pages()
    monkeypatch.setattr(mod, "_current_branch", lambda: "gh-pages")
    monkeypatch.chdir(tmp_path)

    db_size = 8192  # two SQLite pages
    _make_fake_db(tmp_path / "language_atlas.sqlite", size=db_size)
    (tmp_path / "site").mkdir()

    result = mod.main()

    assert result == 0, "main() should succeed"

    db_dir = tmp_path / "site" / "db" / "atlas"
    assert db_dir.exists(), "site/db/atlas/ must be created"
    assert any(db_dir.iterdir()), "site/db/atlas/ must contain at least one file"

    config_path = db_dir / "config.json"
    assert config_path.exists(), "config.json must be written"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    for key in ("serverMode", "url", "databaseLengthBytes"):
        assert key in config, f"config.json must have '{key}' key"

    assert config["databaseLengthBytes"] == db_size, (
        "databaseLengthBytes must equal the actual database file size"
    )

    db_file = db_dir / config["url"]
    assert db_file.exists(), f"database file '{config['url']}' must exist in site/db/atlas/"
