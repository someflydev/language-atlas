#!/usr/bin/env python3
import sqlite3
import json
import os
import argparse
import sys
from pathlib import Path

# Add src to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_ROOT / "src"))

from app.core.insights import AtlasAnalytics

def main():
    parser = argparse.ArgumentParser(description="Atlas Analytics Reporting Suite")
    parser.add_argument(
        "--report", 
        choices=["safety_complexity", "creator_impact", "cluster_genealogy", "innovation_trends", "db_health", "all"],
        default="all",
        help="Specific report to generate"
    )
    parser.add_argument("--db", default=str(REPO_ROOT / "language_atlas.sqlite"), help="Path to SQLite database")
    parser.add_argument("--output-dir", default=str(REPO_ROOT / "data/reports"), help="Directory for report output")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db):
        print(f"Error: Database not found at {args.db}")
        sys.exit(1)
        
    os.makedirs(args.output_dir, exist_ok=True)
    
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    analytics = AtlasAnalytics(conn)
    
    reports_to_run = []
    if args.report == "all":
        reports_to_run = ["safety_complexity", "creator_impact", "cluster_genealogy", "innovation_trends", "db_health"]
    else:
        reports_to_run = [args.report]
        
    for report_key in reports_to_run:
        output_file = Path(args.output_dir) / f"{report_key}.json"
        
        print(f"Generating {report_key} report...")
        
        data = None
        if report_key == "safety_complexity":
            data = analytics.generate_safety_complexity_trends()
            output_file = Path(args.output_dir) / "safety_complexity_trends.json"
        elif report_key == "creator_impact":
            data = analytics.generate_creator_impact()
            output_file = Path(args.output_dir) / "creator_impact.json"
        elif report_key == "cluster_genealogy":
            data = analytics.generate_cluster_genealogy()
            output_file = Path(args.output_dir) / "cluster_genealogy.json"
        elif report_key == "innovation_trends":
            data = analytics.generate_innovation_trends()
            output_file = Path(args.output_dir) / "innovation_trends.json"
        elif report_key == "db_health":
            data = analytics.generate_db_health()
            output_file = Path(args.output_dir) / "db_health.json"
            
        if data is not None:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"Report saved to {output_file}")
            
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
