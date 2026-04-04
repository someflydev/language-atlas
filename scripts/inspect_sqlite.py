#!/usr/bin/env python3
import sqlite3
import os
import sys
import json

# Locate database
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'language_atlas.sqlite'))
if not os.path.exists(DB_PATH):
    print(f"Error: Database not found at {DB_PATH}")
    sys.exit(1)

def print_separator(char='-', length=80):
    print(char * length)

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row['name'] for row in cursor.fetchall()]

    print(f"Found {len(tables)} tables in {os.path.basename(DB_PATH)}\n")

    for table in sorted(tables):
        print_separator('=')
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cursor.fetchone()['count']
        print(f"TABLE: {table} ({count} rows)")
        print_separator('-')

        # Get schema/columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row['name'] for row in cursor.fetchall()]
        print(f"Columns: {', '.join(columns)}")

        if count == 0:
            print("\n(Empty table)\n")
            continue

        # Get 1-2 sample rows
        cursor.execute(f"SELECT * FROM {table} LIMIT 2")
        rows = cursor.fetchall()
        
        print("\nSample Data:")
        for i, row in enumerate(rows, 1):
            row_dict = dict(row)
            # Truncate long strings for better skimming
            for k, v in row_dict.items():
                if isinstance(v, bytes):
                    row_dict[k] = f"<bytes: {len(v)}>"
                elif isinstance(v, str) and len(v) > 100:
                    row_dict[k] = v[:97] + '...'
            
            # Print as formatted JSON for easy reading
            print(f"  Row {i}:")
            formatted = json.dumps(row_dict, indent=4)
            for line in formatted.split('\n'):
                print(f"    {line}")
        
        print("\n")

    conn.close()

if __name__ == "__main__":
    main()
