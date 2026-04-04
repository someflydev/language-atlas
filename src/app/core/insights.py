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

class AtlasAnalytics:
    def __init__(self, db_conn):
        self.conn = db_conn

    def generate_safety_complexity_trends(self):
        """
        Aggregate average complexity_bias (low:1, medium:2, high:3) 
        and safety_model distribution per decade.
        """
        # Mapping: low->1, medium->2, high->3
        query_avg = """
        SELECT 
            (year / 10) * 10 as decade,
            AVG(CASE 
                WHEN LOWER(complexity_bias) = 'low' THEN 1.0
                WHEN LOWER(complexity_bias) = 'medium' THEN 2.0
                WHEN LOWER(complexity_bias) = 'high' THEN 3.0
                ELSE NULL
            END) as avg_complexity
        FROM languages
        WHERE year IS NOT NULL
        GROUP BY decade
        ORDER BY decade ASC;
        """
        
        query_dist = """
        SELECT 
            (year / 10) * 10 as decade,
            safety_model,
            COUNT(*) as lang_count
        FROM languages
        WHERE year IS NOT NULL
        GROUP BY decade, safety_model
        ORDER BY decade ASC;
        """
        
        cursor = self.conn.cursor()
        
        cursor.execute(query_avg)
        trends = {}
        for row in cursor.fetchall():
            decade = str(row['decade'])
            trends[decade] = {
                "avg_complexity": row['avg_complexity'],
                "safety_distribution": {}
            }
            
        cursor.execute(query_dist)
        for row in cursor.fetchall():
            decade = str(row['decade'])
            if decade in trends:
                model = row['safety_model'] or "unknown"
                trends[decade]["safety_distribution"][model] = row['lang_count']
                
        return trends

    def generate_creator_impact(self):
        """
        Rank creators (people) by the total influence_score 
        of all languages they are credited with.
        """
        query = """
        SELECT 
            p.name,
            SUM(l.influence_score) as total_impact,
            COUNT(l.id) as language_count,
            GROUP_CONCAT(l.name, ', ') as languages
        FROM people p
        JOIN language_people lp ON p.id = lp.person_id
        JOIN languages l ON lp.language_id = l.id
        GROUP BY p.name
        ORDER BY total_impact DESC;
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def generate_cluster_genealogy(self):
        """
        For each cluster, calculate the "Internal vs. External Influence" ratio.
        """
        query = """
        SELECT 
            l_src.cluster as source_cluster,
            l_tgt.cluster as target_cluster,
            COUNT(*) as influence_count
        FROM influences i
        JOIN languages l_src ON i.source_id = l_src.id
        JOIN languages l_tgt ON i.target_id = l_tgt.id
        GROUP BY source_cluster, target_cluster;
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        matrix = {}
        for row in cursor.fetchall():
            src = row['source_cluster'] or "unknown"
            tgt = row['target_cluster'] or "unknown"
            if src not in matrix:
                matrix[src] = {"internal": 0, "external": 0, "breakdown": {}}
            
            matrix[src]["breakdown"][tgt] = row['influence_count']
            if src == tgt:
                matrix[src]["internal"] += row['influence_count']
            else:
                matrix[src]["external"] += row['influence_count']
                
        # Calculate ratios
        for cluster, stats in matrix.items():
            total = stats["internal"] + stats["external"]
            stats["ratio"] = stats["internal"] / total if total > 0 else 0
            
        return matrix

    def generate_innovation_trends(self):
        """
        Extract common themes from key_innovations across different generation tags.
        """
        query = """
        SELECT 
            l.generation,
            ps.content as innovations
        FROM languages l
        JOIN language_profiles lp ON l.id = lp.language_id
        JOIN profile_sections ps ON lp.id = ps.profile_id
        WHERE ps.section_name = 'key_innovations';
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        gen_trends = {}
        for row in cursor.fetchall():
            gen = row['generation'] or "unknown"
            if gen not in gen_trends:
                gen_trends[gen] = []
            
            # Basic keyword extraction: split by common separators and clean
            text = row['innovations'].replace('*', '').replace('-', '')
            # Clean up and split into lines or items if possible
            items = [i.strip() for i in text.split('\n') if i.strip()]
            gen_trends[gen].extend(items)
            
        return gen_trends

    def generate_db_health(self):
        """
        Identify orphan, terminal languages and high-influence without profiles.
        """
        # Orphan: no influences in or out
        query_orphans = """
        SELECT name FROM languages
        WHERE id NOT IN (SELECT source_id FROM influences)
        AND id NOT IN (SELECT target_id FROM influences);
        """
        
        # Terminal: influenced by many, but influence none
        query_terminal = """
        SELECT name FROM languages
        WHERE id IN (SELECT target_id FROM influences)
        AND id NOT IN (SELECT source_id FROM influences);
        """
        
        # High influence (>= 5) without profile
        query_missing_profiles = """
        SELECT name, influence_score FROM languages
        WHERE influence_score >= 5
        AND id NOT IN (SELECT language_id FROM language_profiles);
        """
        
        cursor = self.conn.cursor()
        
        cursor.execute(query_orphans)
        orphans = [row['name'] for row in cursor.fetchall()]
        
        cursor.execute(query_terminal)
        terminal = [row['name'] for row in cursor.fetchall()]
        
        cursor.execute(query_missing_profiles)
        missing_profiles = [dict(row) for row in cursor.fetchall()]
        
        return {
            "orphans": orphans,
            "terminal": terminal,
            "high_influence_missing_profiles": missing_profiles,
            "summary": {
                "orphan_count": len(orphans),
                "terminal_count": len(terminal),
                "missing_profile_count": len(missing_profiles)
            }
        }

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
