import pytest
import sqlite3
import os
import sys
from pathlib import Path

# Add src to sys.path
REPO_ROOT = Path(__file__).parent.parent
sys.path.append(str(REPO_ROOT / "src"))

from app.core.data_loader import DataLoader
from app.core.build_sqlite import build_database

@pytest.fixture(scope="session")
def db_conn():
    """Provides a 'Mirror Universe' in-memory SQLite database populated with production data."""
    # Use standard sqlite3 to create an in-memory DB
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    # Populate with data from JSON using the production build logic
    data_dir = str(REPO_ROOT / "data")
    build_database(conn=conn, data_dir=data_dir)
    
    yield conn
    conn.close()

@pytest.fixture
def mock_loader(db_conn, monkeypatch):
    """Provides a DataLoader that uses the in-memory test database."""
    loader = DataLoader()
    # Mock _get_connection to return our in-memory connection
    def mock_get_conn():
        # Re-wrap in a connection that doesn't close the shared in-memory DB if needed
        # Or just return the same connection. sqlite3 :memory: is shared within the same connection object.
        return db_conn
    
    monkeypatch.setattr(loader, "_get_connection", mock_get_conn)
    monkeypatch.setattr(loader, "use_sqlite", True)
    return loader
