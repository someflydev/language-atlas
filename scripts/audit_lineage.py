#!/usr/bin/env python3
import json
import sys
import argparse
from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).parent.parent

def main() -> None:
    parser = argparse.ArgumentParser(description="Language Atlas: Audit Lineage")
    parser.add_argument("--data", type=str, help="Path to languages.json")
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

    all_names = {l["name"] for l in languages}
    broken_references = []
    isolated_islands = []

    print(f"\n\033[1;32m=== Language Atlas: Lineage Audit ===\033[0m")

    for lang in languages:
        name = lang["name"]
        inf_by = lang.get("influenced_by", [])
        inf = lang.get("influenced", [])
        
        # Check broken references in influenced_by
        for ref in inf_by:
            if ref not in all_names:
                broken_references.append((name, "influenced_by", ref))
        
        # Check broken references in influenced
        for ref in inf:
            if ref not in all_names:
                broken_references.append((name, "influenced", ref))
        
        # Check for isolated islands
        # (Zero incoming OR zero outgoing?) 
        # Prompt says "zero incoming AND zero outgoing influences"
        if not inf_by and not inf:
            isolated_islands.append(name)

    if broken_references:
        print(f"\n\033[1;31mFound {len(broken_references)} Broken References:\033[0m")
        for lang_name, field, ref in broken_references:
            print(f" - {lang_name} ({field}): {ref} \033[1;33m(Not Found)\033[0m")
    else:
        print(f"\n\033[1;32mNo broken references found.\033[0m")

    if isolated_islands:
        print(f"\n\033[1;34mFound {len(isolated_islands)} Isolated Islands (0 influences in/out):\033[0m")
        for lang_name in isolated_islands:
            print(f" - {lang_name}")
    else:
        print(f"\n\033[1;32mNo isolated islands found.\033[0m")

if __name__ == "__main__":
    main()
