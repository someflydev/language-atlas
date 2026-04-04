#!/usr/bin/env python3
import json
import sys
import argparse
from pathlib import Path
from collections import Counter

def get_project_root():
    return Path(__file__).parent.parent

def print_table(title, headers, rows):
    print(f"\n\033[1;34m{title}\033[0m")
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))
    
    # Header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))
    
    # Rows
    for row in rows:
        print(" | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row)))

def main():
    parser = argparse.ArgumentParser(description="Language Atlas: Data Statistics")
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

    total_count = len(languages)
    keystones = [l for l in languages if l.get("is_keystone")]
    keystone_count = len(keystones)
    keystone_density = (keystone_count / total_count * 100) if total_count > 0 else 0

    print(f"\n\033[1;32m=== Language Atlas Statistics ===\033[0m")
    print(f"Total Languages: {total_count}")
    print(f"Keystone Languages: {keystone_count} ({keystone_density:.1f}% Keystone Density)")

    # Distributions
    gen_counter = Counter(l.get("generation", "unknown") for l in languages)
    cluster_counter = Counter(l.get("cluster", "unknown") for l in languages)
    safety_counter = Counter(l.get("safety_model", "unknown") for l in languages)

    print_table("Distribution by Generation", ["Generation", "Count", "%"], 
                [[g, c, f"{(c/total_count*100):.1f}%"] for g, c in gen_counter.most_common()])

    print_table("Distribution by Cluster", ["Cluster", "Count", "%"], 
                [[c, count, f"{(count/total_count*100):.1f}%"] for c, count in cluster_counter.most_common()])

    print_table("Distribution by Safety Model", ["Safety Model", "Count", "%"], 
                [[s, c, f"{(c/total_count*100):.1f}%"] for s, c in safety_counter.most_common()])

if __name__ == "__main__":
    main()
