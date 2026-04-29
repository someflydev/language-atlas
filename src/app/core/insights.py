import sqlite3
import json
import os
import statistics
from pathlib import Path
from typing import List, Dict, Any, Protocol

class _Connection(Protocol):
    def execute(self, sql: str, params: Any = ...) -> Any: ...
    def executemany(self, sql: str, seq: Any) -> Any: ...
    def close(self) -> None: ...
    def cursor(self) -> Any: ...

class InsightGenerator:
    def __init__(self, db_conn: _Connection) -> None:
        self.conn = db_conn

    def calculate_influence_depth(self, keystone_language_name: str) -> List[Dict[str, Any]]:
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

    def calculate_paradigm_volatility(self) -> List[Dict[str, Any]]:
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

    def calculate_leverage_scores(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Rank languages by descendant reach per unit of ancestor depth.
        """
        query = """
        WITH descendant_stats AS (
            SELECT
                root_language_id,
                COUNT(descendant_language_id) AS descendant_count,
                MAX(depth) AS max_descendant_depth
            FROM language_descendants
            GROUP BY root_language_id
        ),
        ancestor_stats AS (
            SELECT
                root_language_id,
                MAX(depth) AS max_ancestor_depth
            FROM language_ancestry
            GROUP BY root_language_id
        )
        SELECT
            l.name,
            l.display_name,
            COALESCE(l.entity_type, 'language') AS entity_type,
            l.year,
            COALESCE(ds.descendant_count, 0) AS descendant_count,
            COALESCE(ds.max_descendant_depth, 0) AS max_descendant_depth,
            COALESCE(ast.max_ancestor_depth, 0) AS max_ancestor_depth
        FROM languages l
        JOIN descendant_stats ds ON ds.root_language_id = l.id
        LEFT JOIN ancestor_stats ast ON ast.root_language_id = l.id
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []

        results = []
        for row in rows:
            descendant_count = int(row["descendant_count"] or 0)
            ancestor_depth = int(row["max_ancestor_depth"] or 0)
            leverage = descendant_count / max(ancestor_depth, 1)
            results.append(
                {
                    "name": row["name"],
                    "display_name": row["display_name"] or row["name"],
                    "entity_type": row["entity_type"] or "language",
                    "year": row["year"],
                    "leverage_score": round(leverage, 2),
                    "descendant_count": descendant_count,
                    "max_ancestor_depth": ancestor_depth,
                }
            )

        results.sort(
            key=lambda item: (
                -float(item["leverage_score"]),
                -int(item["descendant_count"]),
                str(item["name"]).lower(),
            )
        )
        return results[:limit]

    def calculate_concept_diffusion(self) -> List[Dict[str, Any]]:
        """
        Rank paradigms by direct adoption plus transitive downstream reach.
        """
        diffusion_query = """
        SELECT
            p.id AS paradigm_id,
            p.name AS paradigm_name,
            COUNT(DISTINCT lp.language_id) AS direct_languages,
            COUNT(DISTINCT la.root_language_id) AS carrier_descendants
        FROM paradigms p
        JOIN language_paradigms lp ON lp.paradigm_id = p.id
        LEFT JOIN language_ancestry la ON la.ancestor_language_id = lp.language_id
        GROUP BY p.id, p.name
        """
        carrier_query = """
        SELECT
            l.name,
            l.year,
            COUNT(DISTINCT ld.descendant_language_id) AS reachability_score
        FROM language_paradigms lp
        JOIN languages l ON l.id = lp.language_id
        LEFT JOIN language_descendants ld ON ld.root_language_id = l.id
        WHERE lp.paradigm_id = ?
        GROUP BY l.id, l.name, l.year
        ORDER BY reachability_score DESC, l.year ASC, l.name ASC
        LIMIT 1
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(diffusion_query)
            rows = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []

        results = []
        for row in rows:
            direct_languages = int(row["direct_languages"] or 0)
            carrier_descendants = int(row["carrier_descendants"] or 0)
            cursor.execute(carrier_query, (row["paradigm_id"],))
            carrier = cursor.fetchone()
            results.append(
                {
                    "paradigm_name": row["paradigm_name"],
                    "direct_languages": direct_languages,
                    "diffusion_score": direct_languages + carrier_descendants,
                    "primary_carrier_name": carrier["name"] if carrier else None,
                    "primary_carrier_year": carrier["year"] if carrier else None,
                }
            )

        results.sort(
            key=lambda item: (
                -int(item["diffusion_score"]),
                str(item["paradigm_name"]).lower(),
            )
        )
        return results

    def detect_graph_anomalies(self) -> Dict[str, Any]:
        """
        Detect deep chains, generation-local reachability outliers, and era gaps.
        """
        empty = {"deep_chains": [], "outliers": [], "era_gaps": []}
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT path_text, depth
                FROM language_lineage_paths_bounded
                WHERE depth >= 7
                ORDER BY depth DESC, path_text ASC
                LIMIT 5
                """
            )
            deep_chains = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                """
                WITH reachability AS (
                    SELECT
                        root_language_id,
                        COUNT(descendant_language_id) AS reachability_score
                    FROM language_descendants
                    GROUP BY root_language_id
                )
                SELECT
                    l.name,
                    l.generation,
                    COALESCE(r.reachability_score, 0) AS reachability_score
                FROM languages l
                LEFT JOIN reachability r ON r.root_language_id = l.id
                WHERE l.generation IS NOT NULL
                """
            )
            reachability_rows = [dict(row) for row in cursor.fetchall()]

        except sqlite3.OperationalError:
            return empty

        by_generation: Dict[str, List[Dict[str, Any]]] = {}
        for row in reachability_rows:
            generation = row.get("generation")
            if generation:
                by_generation.setdefault(generation, []).append(row)

        outliers = []
        for generation, rows in by_generation.items():
            if len(rows) < 3:
                continue
            scores = [int(row["reachability_score"] or 0) for row in rows]
            stdev = statistics.stdev(scores)
            if stdev == 0:
                continue
            avg = statistics.mean(scores)
            for row in rows:
                score = int(row["reachability_score"] or 0)
                z_score = (score - avg) / stdev
                if z_score > 2:
                    outliers.append(
                        {
                            "name": row["name"],
                            "generation": generation,
                            "reachability_score": score,
                            "generation_mean": round(avg, 2),
                            "z_score": round(z_score, 2),
                        }
                    )
        outliers.sort(key=lambda item: (-float(item["z_score"]), item["name"]))

        generation_order = ["dawn", "early", "web1", "cloud", "renaissance", "autonomic"]
        era_gaps = []
        for from_generation, to_generation in zip(generation_order, generation_order[1:]):
            try:
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT later.id) AS connected_count
                    FROM languages later
                    JOIN language_ancestry la ON la.root_language_id = later.id
                    JOIN languages earlier ON earlier.id = la.ancestor_language_id
                    WHERE earlier.generation = ?
                      AND later.generation = ?
                    """,
                    (from_generation, to_generation),
                )
                connected_count = int(cursor.fetchone()["connected_count"] or 0)
            except sqlite3.OperationalError:
                return empty
            if connected_count < 3:
                era_gaps.append(
                    {
                        "from_generation": from_generation,
                        "to_generation": to_generation,
                        "connected_count": connected_count,
                    }
                )

        return {
            "deep_chains": deep_chains,
            "outliers": outliers,
            "era_gaps": era_gaps,
        }

    def generate_all_insights(self) -> Dict[str, Any]:
        """
        Generates all insights and returns a dictionary.
        """
        # Keystone languages for influence depth
        keystones = ["ALGOL 60", "Lisp", "C", "Smalltalk", "Haskell"]
        
        influence_data: Dict[str, List[Dict[str, Any]]] = {}
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

    def stamp_to_json(self, output_path: str) -> Dict[str, Any]:
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
    def __init__(self, db_conn: _Connection) -> None:
        self.conn = db_conn

    def generate_safety_complexity_trends(self) -> Dict[str, Dict[str, Any]]:
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
        trends: Dict[str, Dict[str, Any]] = {}
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

    def generate_creator_impact(self) -> List[Dict[str, Any]]:
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

    def generate_cluster_genealogy(self) -> Dict[str, Dict[str, Any]]:
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
        
        matrix: Dict[str, Dict[str, Any]] = {}
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

    def generate_innovation_trends(self) -> Dict[str, List[str]]:
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
        
        gen_trends: Dict[str, List[str]] = {}
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

    def generate_db_health(self) -> Dict[str, Any]:
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
        generator.stamp_to_json(str(REPO_ROOT / "generated-reports/historical_insights.json"))
        conn.close()
    else:
        print(f"Database not found at {DB_PATH}")
