"""Prepare GitHub Pages deployment artifacts.

This script must be run on the gh-pages branch only. It copies the
SQLite database as a single asset ready for sql.js-httpvfs HTTP range
requests, writes the accompanying config.json, writes .nojekyll at the
repo root, and writes the root redirect index.html.

Usage (from repo root, on gh-pages branch):
    uv run python scripts/prep_pages.py

The script refuses to run on the main branch to prevent accidental
build artifact commits to the development branch.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


# HTTP range-request chunk size for sql.js-httpvfs (chunked server mode).
# The browser fetches only the 4 KiB pages it needs for each query.
_REQUEST_CHUNK_SIZE = 4096

_INDEX_HTML = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url=site/">
    <title>Language Atlas</title>
    <link rel="canonical" href="site/">
  </head>
  <body>
    <p>Redirecting to <a href="site/">Language Atlas</a>.</p>
  </body>
</html>
"""


def _current_branch() -> str:
    """Return the current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main() -> int:
    """Run the pages preparation pipeline.

    All paths are resolved relative to the current working directory so
    that tests can use monkeypatch.chdir() to redirect I/O to a tmp dir.
    """
    repo_root = Path.cwd()
    db_src = repo_root / "language_atlas.sqlite"
    site_dir = repo_root / "site"
    site_db_dir = repo_root / "site" / "db" / "atlas"
    index_html = repo_root / "index.html"
    nojekyll = repo_root / ".nojekyll"

    # 1. Branch guard
    branch = _current_branch()
    if branch == "main":
        print(
            "Refusing to build pages artifacts on main; "
            "switch to gh-pages first.",
            file=sys.stderr,
        )
        return 1

    # 2. Verify database exists
    if not db_src.exists():
        print(
            f"Database not found: {db_src}\n"
            "Run 'make build' first.",
            file=sys.stderr,
        )
        return 1

    # 3. Verify site/ exists
    if not site_dir.exists():
        print(
            f"Static site directory not found: {site_dir}\n"
            "Run 'make site' first.",
            file=sys.stderr,
        )
        return 1

    # 4. Copy database and write config.json
    #
    # sql.js-httpvfs "chunked" server mode: the browser fetches only the
    # SQLite pages it needs via HTTP range requests. GitHub Pages supports
    # range requests, so this keeps page loads fast even for large databases.
    # The database is served as a single file; no splitting is required.
    site_db_dir.mkdir(parents=True, exist_ok=True)
    db_dest = site_db_dir / "db.sqlite3"
    shutil.copy2(db_src, db_dest)
    db_size = db_dest.stat().st_size

    config: dict = {
        "serverMode": "chunked",
        "requestChunkSize": _REQUEST_CHUNK_SIZE,
        "databaseLengthBytes": db_size,
        "url": "db.sqlite3",
    }
    config_path = site_db_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    # 5. Write .nojekyll (prevents GitHub Pages from running Jekyll)
    nojekyll.touch()

    # 6. Write root redirect index.html
    index_html.write_text(_INDEX_HTML, encoding="utf-8")

    # 7. Summary
    site_files = [f for f in site_dir.rglob("*") if f.is_file()]
    site_file_count = len(site_files)
    site_total_bytes = sum(f.stat().st_size for f in site_files)

    print(f"Pages artifacts prepared on branch: {branch}")
    print(f"  Database:    {db_dest} ({db_size:,} bytes)")
    print(f"  Config:      {config_path}")
    print(f"  Server mode: {config['serverMode']} "
          f"(chunk size: {_REQUEST_CHUNK_SIZE} bytes)")
    print(f"  .nojekyll:   {nojekyll}")
    print(f"  index.html:  {index_html}")
    print(f"  site/ files: {site_file_count} files ({site_total_bytes:,} bytes)")
    print()
    print("Next steps:")
    sha_result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True
    )
    sha = sha_result.stdout.strip() if sha_result.returncode == 0 else "<sha>"
    print("  git add site language_atlas.sqlite .nojekyll index.html")
    print(f'  git commit -m "[gh-pages] Refresh from main @ {sha}"')
    print("  git push origin gh-pages")
    print("  git checkout main")

    return 0


if __name__ == "__main__":
    sys.exit(main())
