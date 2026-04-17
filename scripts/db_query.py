#!/usr/bin/env python3
import sqlite3
import sys
import argparse
from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).parent.parent

def main() -> None:
    parser = argparse.ArgumentParser(description="Language Atlas: SQLite Query Tool")
    parser.add_argument("query", type=str, help="SQL query to execute")
    parser.add_argument("--db", type=str, help="Path to SQLite database")
    args = parser.parse_args()

    root = get_project_root()
    # Search for database in common locations
    db_candidates = []
    if args.db:
        db_candidates.append(Path(args.db))
    else:
        db_candidates = [
            root / "language_atlas.sqlite",
            root / "data" / "language_atlas.sqlite"
        ]

    db_path = None
    for cand in db_candidates:
        if cand.exists():
            db_path = cand
            break
    
    if not db_path:
        print(f"\033[1;31mError: SQLite database not found. Searched candidates: {', '.join(str(c) for c in db_candidates)}\033[0m")
        sys.exit(1)

    print(f"\033[1;34mConnected to: {db_path}\033[0m")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(args.query)
        
        # Check if it was a SELECT or similar
        if cursor.description:
            headers = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Simple table formatting
            if rows:
                widths = [len(h) for h in headers]
                for row in rows:
                    for i, val in enumerate(row):
                        widths[i] = max(widths[i], len(str(val)))
                
                header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
                print(f"\n\033[1;32m{header_line}\033[0m")
                print("-" * len(header_line))
                for row in rows:
                    print(" | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row)))
                print(f"\n({len(rows)} rows returned)")
            else:
                print("\n(Empty result set)")
        else:
            conn.commit()
            print(f"\nQuery executed successfully. Changes: {conn.total_changes}")
            
    except Exception as e:
        print(f"\033[1;31mSQL Error: {e}\033[0m")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
