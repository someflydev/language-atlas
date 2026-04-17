#!/usr/bin/env python3
import json
import sys
import argparse
import datetime
from pathlib import Path
from typing import Any

def get_project_root() -> Path:
    return Path(__file__).parent.parent

def main() -> None:
    current_year = datetime.datetime.now().year
    parser = argparse.ArgumentParser(description="Language Atlas: Data Integrity Check")
    parser.add_argument("--data", type=str, help="Path to languages.json")
    parser.add_argument("--min-year", type=int, default=1940, help="Minimum valid year (default: 1940)")
    parser.add_argument("--max-year", type=int, default=current_year, help="Maximum valid year (default: current)")
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

    print(f"\n\033[1;32m=== Language Atlas: Integrity Check ===\033[0m")
    print(f"Scanning {len(languages)} entries...")

    issues: list[tuple[str, str]] = []

    fields_to_check = [
        "name", "year", "creators", "paradigms", "cluster", "generation",
        "primary_use_cases", "key_innovations", "influenced_by", "influenced",
        "philosophy", "mental_model", "complexity_bias", "safety_model",
        "typing_discipline", "memory_management", "display_name"
    ]

    for lang in languages:
        name = lang.get("name", "Unknown")
        
        # 1. Field existence and emptiness
        for field in fields_to_check:
            val = lang.get(field)
            if val is None:
                issues.append((name, f"Missing field: {field}"))
            elif isinstance(val, (list, str)) and len(val) == 0:
                issues.append((name, f"Empty field: {field}"))
        
        # 2. Year bounds
        year = lang.get("year")
        if isinstance(year, int):
            if year < args.min_year or year > args.max_year:
                issues.append((name, f"Year out of bounds: {year} (Range: {args.min_year}-{args.max_year})"))
        elif year is not None:
            issues.append((name, f"Invalid year type: {type(year).__name__}"))

    if issues:
        print(f"\n\033[1;31mFound {len(issues)} integrity issues:\033[0m")
        # Group by language for better output
        grouped: dict[str, list[str]] = {}
        for lang_name, issue in issues:
            if lang_name not in grouped:
                grouped[lang_name] = []
            grouped[lang_name].append(issue)
        
        for lang_name, lang_issues in sorted(grouped.items()):
            print(f" - \033[1;33m{lang_name}\033[0m:")
            for issue in lang_issues:
                print(f"   * {issue}")
    else:
        print(f"\n\033[1;32mIntegrity check passed! All entries look healthy.\033[0m")

if __name__ == "__main__":
    main()
