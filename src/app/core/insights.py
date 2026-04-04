import sqlite3
import json
import os
from pathlib import Path

class InsightGenerator:
    def __init__(self, db_conn):
        self.conn = db_conn

    def calculate_influence_depth(self, keystone_language_name):
        """
        Uses a Recursive CTE to calculate the transitive influence of a keystone language.
        Returns the list of influenced languages and their distance.
        """
        query = """
        WITH RECURSIVE influence_chain(id, name, depth) AS (
            SELECT id, name, 0 FROM languages WHERE name = ?
            UNION ALL
            SELECT l.id, l.name, ic.depth + 1
            FROM languages l
            JOIN influences i ON l.id = i.target_id
            JOIN influence_chain ic ON i.source_id = ic.id
            WHERE ic.depth < 10 -- Safety limit
        )
        SELECT name, MIN(depth) as distance
        FROM influence_chain
        GROUP BY name
        ORDER BY distance ASC, name ASC;
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (keystone_language_name,))
        return [dict(row) for row in cursor.fetchall()]

    def calculate_paradigm_volatility(self):
        """
        Calculates which decades saw the most rapid introduction of new paradigms
        using Window Functions to rank them.
        """
        query = """
        WITH paradigm_first_appearance AS (
            SELECT 
                p.name as paradigm_name, 
                MIN(l.year) as first_appearance_year
            FROM paradigms p
            JOIN language_paradigms lp ON p.id = lp.paradigm_id
            JOIN languages l ON lp.language_id = l.id
            WHERE l.year IS NOT NULL
            GROUP BY p.name
        ),
        decade_stats AS (
            SELECT 
                (first_appearance_year / 10) * 10 as decade,
                COUNT(*) as new_paradigm_count
            FROM paradigm_first_appearance
            GROUP BY decade
        )
        SELECT 
            decade, 
            new_paradigm_count,
            RANK() OVER (ORDER BY new_paradigm_count DESC) as volatility_rank,
            AVG(new_paradigm_count) OVER (ORDER BY decade ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as rolling_avg
        FROM decade_stats
        WHERE decade IS NOT NULL
        ORDER BY decade ASC;
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def generate_all_insights(self):
        """
        Generates all insights and returns a dictionary.
        """
        # Keystone languages for influence depth
        keystones = ["ALGOL 60", "Lisp", "C", "Smalltalk", "Haskell"]
        
        influence_data = {}
        for k in keystones:
            influence_data[k] = self.calculate_influence_depth(k)
            
        return {
            "metadata": {
                "description": "Historical insights generated from the Language Atlas",
                "engine": "SQLite Recursive CTEs & Window Functions"
            },
            "influence_depth": influence_data,
            "paradigm_volatility": self.calculate_paradigm_volatility()
        }

    def stamp_to_json(self, output_path):
        """
        Stamps the insights out as a JSON artifact.
        """
        insights = self.generate_all_insights()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(insights, f, indent=2)
            
        print(f"Stamped insights to {output_path}")
        return insights

if __name__ == "__main__":
    # If run directly, we need a DB connection.
    # Root is 3 levels up from src/app/core/insights.py
    REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    DB_PATH = REPO_ROOT / "language_atlas.sqlite"
    
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        generator = InsightGenerator(conn)
        generator.stamp_to_json(str(REPO_ROOT / "data/reports/historical_insights.json"))
        conn.close()
    else:
        print(f"Database not found at {DB_PATH}")
