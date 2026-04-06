import sqlite3
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Get the project root directory (one level up from scripts/)
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
DB_PATH: Path = ROOT_DIR / "language_atlas.sqlite"
OUTPUT_DIR: Path = ROOT_DIR / "generated-docs"

def setup_directories() -> None:
    """Create necessary directories for generated documentation."""
    (OUTPUT_DIR / "languages").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "eras").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "paradigms").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "concepts").mkdir(parents=True, exist_ok=True)

def get_db_connection() -> sqlite3.Connection:
    """Establish connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_language_profiles(conn: sqlite3.Connection) -> None:
    """Generate individual Markdown files for each language."""
    # Fetch languages and their profile title/overview
    query = """
        SELECT l.*, lp.title as profile_title, lp.overview as profile_overview
        FROM languages l
        LEFT JOIN language_profiles lp ON l.id = lp.language_id
    """
    languages = conn.execute(query).fetchall()
    
    for lang in languages:
        lang_id = lang["id"]
        lang_name = lang["name"]
        display_name = lang["display_name"]
        profile_title = lang["profile_title"] if lang["profile_title"] else display_name
        
        # Get influences
        influences_query = """
            SELECT l.display_name 
            FROM influences i
            JOIN languages l ON i.source_id = l.id
            WHERE i.target_id = ?
        """
        influenced_by: List[str] = [row["display_name"] for row in conn.execute(influences_query, (lang_id,)).fetchall()]
        
        influenced_query = """
            SELECT l.display_name 
            FROM influences i
            JOIN languages l ON i.target_id = l.id
            WHERE i.source_id = ?
        """
        influenced_others: List[str] = [row["display_name"] for row in conn.execute(influenced_query, (lang_id,)).fetchall()]
        
        # Get paradigms
        paradigms_query = """
            SELECT p.name 
            FROM language_paradigms lp
            JOIN paradigms p ON lp.paradigm_id = p.id
            WHERE lp.language_id = ?
        """
        paradigms: List[str] = [row["name"] for row in conn.execute(paradigms_query, (lang_id,)).fetchall()]
        
        # Get creators
        creators_query = """
            SELECT p.name, lp.role
            FROM language_people lp
            JOIN people p ON lp.person_id = p.id
            WHERE lp.language_id = ?
        """
        creators: List[str] = [f"{row['name']} ({row['role']})" for row in conn.execute(creators_query, (lang_id,)).fetchall()]
        
        # Get sections
        sections_query = """
            SELECT ps.section_name, ps.content
            FROM profile_sections ps
            JOIN language_profiles lp ON ps.profile_id = lp.id
            WHERE lp.language_id = ?
        """
        sections = conn.execute(sections_query, (lang_id,)).fetchall()
        
        # Build Frontmatter
        frontmatter: Dict[str, Any] = {
            "title": display_name,
            "year": lang["year"],
            "cluster": lang["cluster"],
            "generation": lang["generation"],
            "paradigms": paradigms,
            "creators": creators,
            "is_keystone": bool(lang["is_keystone"]),
            "typing_discipline": lang["typing_discipline"],
            "memory_management": lang["memory_management"],
            "safety_model": lang["safety_model"]
        }
        
        # Write file
        safe_name = lang_name.replace(" ", "_").replace("/", "_")
        file_path = OUTPUT_DIR / "languages" / f"{safe_name}.md"
        with open(file_path, "w", encoding='utf-8') as f:
            f.write("---\n")
            f.write(json.dumps(frontmatter, indent=2))
            f.write("\n---\n\n")
            f.write(f"# {profile_title}\n\n")
            
            if lang['profile_overview']:
                f.write(f"{lang['profile_overview']}\n\n")
            
            f.write(f"## Philosophy\n{lang['philosophy']}\n\n")
            f.write(f"## Mental Model\n{lang['mental_model']}\n\n")
            
            if sections:
                for section in sections:
                    title = section["section_name"].replace("_", " ").title()
                    f.write(f"## {title}\n{section['content']}\n\n")
            
            f.write("## Relationships\n")
            if influenced_by:
                f.write(f"- **Influenced by:** {', '.join(influenced_by)}\n")
            if influenced_others:
                f.write(f"- **Influenced:** {', '.join(influenced_others)}\n")
            if not influenced_by and not influenced_others:
                f.write("- No documented direct influences.\n")
            f.write("\n")
            
            f.write("## Technical Details\n")
            f.write(f"- **Typing:** {lang['typing_discipline']}\n")
            f.write(f"- **Memory Management:** {lang['memory_management']}\n")
            f.write(f"- **Safety Model:** {lang['safety_model']}\n")
            f.write(f"- **Complexity Bias:** {lang['complexity_bias']}\n")

def generate_concept_profiles(conn: sqlite3.Connection) -> None:
    """Generate individual Markdown files for each concept."""
    query = """
        SELECT c.*, cp.title as profile_title, cp.overview as profile_overview
        FROM concepts c
        LEFT JOIN concept_profiles cp ON c.id = cp.concept_id
    """
    concepts = conn.execute(query).fetchall()
    
    for concept in concepts:
        concept_id = concept["id"]
        concept_name = concept["name"]
        profile_title = concept["profile_title"] if concept["profile_title"] else concept_name
        
        # Get sections
        sections_query = """
            SELECT cps.section_name, cps.content
            FROM concept_profile_sections cps
            JOIN concept_profiles cp ON cps.profile_id = cp.id
            WHERE cp.concept_id = ?
        """
        sections = conn.execute(sections_query, (concept_id,)).fetchall()
        
        # Write file
        safe_name = concept_name.replace(" ", "_").replace("/", "_")
        file_path = OUTPUT_DIR / "concepts" / f"{safe_name}.md"
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(f"# {profile_title}\n\n")
            
            if concept['profile_overview']:
                f.write(f"{concept['profile_overview']}\n\n")
            
            f.write(f"## Description\n{concept['description']}\n\n")
            
            if sections:
                for section in sections:
                    title = section["section_name"].replace("_", " ").title()
                    f.write(f"## {title}\n{section['content']}\n\n")

def generate_index_files(conn: sqlite3.Connection) -> None:
    """Generate index files for Paradigms and Eras."""
    # Paradigm Index
    paradigms = conn.execute("SELECT * FROM paradigms ORDER BY name").fetchall()
    with open(OUTPUT_DIR / "paradigms.md", "w", encoding='utf-8') as f:
        f.write("# Languages by Paradigm\n\n")
        for p in paradigms:
            f.write(f"## {p['name']}\n")
            desc = p['description'] if p['description'] else "No description available."
            f.write(f"{desc}\n\n")
            
            langs_query = """
                SELECT l.display_name, l.name
                FROM language_paradigms lp
                JOIN languages l ON lp.language_id = l.id
                WHERE lp.paradigm_id = ?
                ORDER BY l.year
            """
            langs = conn.execute(langs_query, (p["id"],)).fetchall()
            if langs:
                for lang in langs:
                    safe_name = lang['name'].replace(" ", "_").replace("/", "_")
                    f.write(f"- [{lang['display_name']}](languages/{safe_name}.md)\n")
            else:
                f.write("- No languages listed.\n")
            f.write("\n")

    # Era/Generation Index
    generations_query = "SELECT DISTINCT generation FROM languages ORDER BY year"
    generations = conn.execute(generations_query).fetchall()
    
    with open(OUTPUT_DIR / "eras.md", "w", encoding='utf-8') as f:
        f.write("# Languages by Era (Generation)\n\n")
        for gen_row in generations:
            gen = gen_row["generation"]
            if not gen: continue
            
            f.write(f"## {gen.title()}\n")
            
            langs_query = """
                SELECT display_name, name, year
                FROM languages
                WHERE generation = ?
                ORDER BY year
            """
            langs = conn.execute(langs_query, (gen,)).fetchall()
            for lang in langs:
                safe_name = lang['name'].replace(" ", "_").replace("/", "_")
                f.write(f"- [{lang['display_name']}](languages/{safe_name}.md) ({lang['year']})\n")
            f.write("\n")

def generate_thematic_docs(conn: sqlite3.Connection) -> None:
    """Generate thematic overview documents (Crossroads, Reactions, etc.)."""
    # 1. Crossroads
    crossroads = conn.execute("SELECT * FROM crossroads").fetchall()
    with open(OUTPUT_DIR / "CROSSROADS.md", "w", encoding='utf-8') as f:
        f.write("# The Crossroads of Computing\n\n")
        for cr in crossroads:
            f.write(f"## {cr['title']}\n{cr['explanation']}\n\n")

    # 2. Modern Reactions
    reactions = conn.execute("SELECT * FROM modern_reactions").fetchall()
    with open(OUTPUT_DIR / "MODERN_REACTIONS.md", "w", encoding='utf-8') as f:
        f.write("# Modern Reactions in Language Design\n\n")
        for mr in reactions:
            f.write(f"## {mr['theme']}\n{mr['explanation']}\n\n")

    # 3. Paradigm Matrix
    matrix = conn.execute("SELECT * FROM paradigm_matrix_dimensions").fetchall()
    with open(OUTPUT_DIR / "PARADIGM_MATRIX.md", "w", encoding='utf-8') as f:
        f.write("# The Paradigm Matrix: Technical Dimensions\n\n")
        for m in matrix:
            f.write(f"## {m['axis']}\n{m['details']}\n\n")

    # 4. Timeline
    periods = conn.execute("SELECT * FROM timeline_periods").fetchall()
    with open(OUTPUT_DIR / "TIMELINE.md", "w", encoding='utf-8') as f:
        f.write("# The Chronological Atlas: Major Events\n\n")
        for p in periods:
            f.write(f"## {p['era_or_period']}\n")
            events = conn.execute("SELECT * FROM timeline_events WHERE period_id = ?", (p["id"],)).fetchall()
            for e in events:
                if e['year']:
                    f.write(f"- **{e['year']}:** {e['description']}\n")
                else:
                    f.write(f"{e['description']}\n")
                
                related = conn.execute("SELECT related_name FROM timeline_event_related WHERE event_id = ?", (e["id"],)).fetchall()
                if related:
                    f.write(f"  * [Related: {', '.join([r['related_name'] for r in related])}]\n")
            f.write("\n")

    # 5. Concepts Summary
    with open(OUTPUT_DIR / "CONCEPTS.md", "w", encoding='utf-8') as f:
        f.write("# Core Concepts: The Soul of Computation\n\n")
        concepts = conn.execute("SELECT name, description FROM concepts").fetchall()
        for c in concepts:
            safe_name = c['name'].replace(" ", "_").replace("/", "_")
            f.write(f"## [{c['name']}](concepts/{safe_name}.md)\n")
            f.write(f"{c['description']}\n\n")

def generate_era_summaries(conn: sqlite3.Connection) -> None:
    """Generate summary files for each Era."""
    eras = conn.execute("SELECT * FROM era_summaries").fetchall()
    for era in eras:
        file_path = OUTPUT_DIR / "eras" / f"{era['slug']}.md"
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(f"# {era['title']}\n\n")
            f.write(f"## Overview\n{era['overview']}\n\n")
            
            # Key Drivers
            drivers = conn.execute("SELECT * FROM era_key_drivers WHERE era_id = ?", (era["id"],)).fetchall()
            if drivers:
                f.write("## Key Drivers\n")
                for d in drivers:
                    f.write(f"- **{d['name']}** {d['description']}\n")
                f.write("\n")
                
            # Pivotal Languages
            pivotal = conn.execute("SELECT * FROM era_pivotal_languages WHERE era_id = ?", (era["id"],)).fetchall()
            if pivotal:
                f.write("## Pivotal Languages\n")
                for p in pivotal:
                    f.write(f"- **{p['name']}** {p['description']}\n")
                f.write("\n")
                
            f.write(f"## Legacy Impact\n{era['legacy_impact']}\n\n")
            if era['diagram']:
                f.write(f"## Diagram Concept\n{era['diagram']}\n\n")

def main() -> None:
    print("Setting up directories...")
    setup_directories()
    
    conn = get_db_connection()
    try:
        print("Generating language profiles...")
        generate_language_profiles(conn)
        
        print("Generating concept profiles...")
        generate_concept_profiles(conn)
        
        print("Generating era summaries...")
        generate_era_summaries(conn)
        
        print("Generating thematic documents...")
        generate_thematic_docs(conn)
        
        print("Generating index files...")
        generate_index_files(conn)
        
        print("Documentation generation complete.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
