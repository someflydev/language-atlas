"""Thin CLI wrapper. Real logic lives in src/app/core/site_builder.py."""
from pathlib import Path
import os, sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("USE_SQLITE", "1")
from app.core.data_loader import DataLoader
from app.core.site_builder import SiteBuilder

ROOT = Path(__file__).resolve().parent.parent
def main() -> None:
    loader = DataLoader()
    SiteBuilder(loader, ROOT / "generated-docs").build_markdown()
    print("Documentation generation complete.")

if __name__ == "__main__":
    main()
