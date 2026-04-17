import pytest
import sqlite3
import os
import sys
from pathlib import Path
from typing import Any, Generator

from pytest import MonkeyPatch

# Add src to sys.path
REPO_ROOT = Path(__file__).parent.parent
sys.path.append(str(REPO_ROOT / "src"))

from app.core.data_loader import DataLoader
from app.core.build_sqlite import build_database

class NoCloseConnection:
    """Wrapper for sqlite3.Connection that ignores close() calls to keep in-memory DB alive."""
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)
    def close(self) -> None:
        # Do nothing to keep the :memory: database alive across DataLoader calls
        pass

@pytest.fixture(scope="session")
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    """Provides a 'Mirror Universe' in-memory SQLite database populated with production data."""
    # Use standard sqlite3 to create an in-memory DB
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Populate with data from JSON using the production build logic
    data_dir = str(REPO_ROOT / "data")
    build_database(conn=conn, data_dir=data_dir)
    
    yield conn
    conn.close()

@pytest.fixture
def mock_loader(db_conn: sqlite3.Connection, monkeypatch: MonkeyPatch) -> DataLoader:
    """Provides a DataLoader that uses the in-memory test database."""
    loader = DataLoader()
    # Mock _get_connection to return our in-memory connection wrapped to avoid closing
    def mock_get_conn() -> NoCloseConnection:
        return NoCloseConnection(db_conn)
    
    monkeypatch.setattr(loader, "_get_connection", mock_get_conn)
    monkeypatch.setattr(loader, "use_sqlite", True)
    return loader
