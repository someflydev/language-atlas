#!/usr/bin/env python3
import json
import csv
import sys
import argparse
from pathlib import Path

def get_project_root():
    return Path(__file__).parent.parent

def main():
    parser = argparse.ArgumentParser(description="Language Atlas: Export Summary")
    parser.add_argument("--data", type=str, help="Path to languages.json")
    parser.add_argument("--format", choices=["csv", "md"], default="csv", help="Output format (csv or md, default: csv)")
    parser.add_argument("--output", type=str, help="Output file path (default: stdout)")
    args = parser.parse_args()

    root = get_project_root()
    data_path = Path(args.data) if args.data else root / "data" / "languages.json"

    if not data_path.exists():
        print(f"\033[1;31mError: Data file not found at {data_path}\033[0m")
        sys.exit(1)

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            languages = json.load(f)
    except Exception as e:
        print(f"\033[1;31mError loading JSON: {e}\033[0m")
        sys.exit(1)

    # Sort by year
    languages.sort(key=lambda x: x.get("year", 0))

    headers = ["Name", "Year", "Creators", "Generation", "Cluster", "Keystone"]
    rows = []
    for lang in languages:
        rows.append([
            lang.get("display_name", lang.get("name", "Unknown")),
            lang.get("year", "Unknown"),
            ", ".join(lang.get("creators", [])),
            lang.get("generation", "Unknown"),
            lang.get("cluster", "Unknown"),
            "Yes" if lang.get("is_keystone") else "No"
        ])

    out = sys.stdout
    if args.output:
        out = open(args.output, "w", encoding="utf-8")

    try:
        if args.format == "csv":
            writer = csv.writer(out)
            writer.writerow(headers)
            writer.writerows(rows)
        elif args.format == "md":
            # Header
            out.write(f"| {' | '.join(headers)} |\n")
            out.write(f"| {' | '.join(['---'] * len(headers))} |\n")
            # Rows
            for row in rows:
                out.write(f"| {' | '.join(str(val) for val in row)} |\n")
    finally:
        if args.output:
            out.close()
            print(f"\n\033[1;32mExported summary to {args.output}\033[0m")

if __name__ == "__main__":
    main()
