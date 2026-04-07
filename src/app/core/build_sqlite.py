#!/usr/bin/env python3
import sqlite3
import os
import sys
from typing import Optional, Dict, List, Set, Tuple, Any

# Ensure we can import from src
# This script is in src/app/core/build_sqlite.py
# Root is 3 levels up
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(os.path.join(REPO_ROOT, 'src'))

from app.core.data_loader import DataLoader

DB_PATH = os.path.join(REPO_ROOT, 'language_atlas.sqlite')

def build_database(conn: Optional[sqlite3.Connection] = None, data_dir: Optional[str] = None) -> None:
    # Force use_sqlite=0 for the loader used during build to ensure it reads from JSON
    os.environ['USE_SQLITE'] = '0'
    if data_dir:
        loader = DataLoader(data_dir=data_dir)
    else:
        print(f"Loading data from JSON...")
        loader = DataLoader()
    
    # Reset USE_SQLITE if needed or just leave it for this process
    os.environ['USE_SQLITE'] = '1'
    
    # 2. Drop and recreate DB
    close_conn = False
    if conn is None:
        if os.path.exists(DB_PATH):
            print(f"Removing existing database at {DB_PATH}")
            os.remove(DB_PATH)
            
        print(f"Creating new database at {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        close_conn = True
    
    try:
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 3. Create Tables
        print("Creating tables...")
        cursor.executescript("""
        CREATE TABLE languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT,
            year INTEGER,
            cluster TEXT,
            generation TEXT,
            philosophy TEXT,
            description TEXT,
            mental_model TEXT,
            complexity_bias TEXT,
            safety_model TEXT,
            typing_discipline TEXT,
            memory_management TEXT,
            is_keystone BOOLEAN,
            influence_score INTEGER DEFAULT 0
        );

        CREATE TABLE paradigms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );

        CREATE TABLE people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE influences (
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            PRIMARY KEY (source_id, target_id),
            FOREIGN KEY (source_id) REFERENCES languages(id),
            FOREIGN KEY (target_id) REFERENCES languages(id)
        );

        CREATE TABLE language_paradigms (
            language_id INTEGER NOT NULL,
            paradigm_id INTEGER NOT NULL,
            PRIMARY KEY (language_id, paradigm_id),
            FOREIGN KEY (language_id) REFERENCES languages(id),
            FOREIGN KEY (paradigm_id) REFERENCES paradigms(id)
        );

        CREATE TABLE language_people (
            language_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            role TEXT,
            PRIMARY KEY (language_id, person_id, role),
            FOREIGN KEY (language_id) REFERENCES languages(id),
            FOREIGN KEY (person_id) REFERENCES people(id)
        );

        CREATE TABLE language_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language_id INTEGER NOT NULL UNIQUE,
            title TEXT,
            overview TEXT,
            FOREIGN KEY (language_id) REFERENCES languages(id)
        );

        CREATE TABLE profile_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            content TEXT,
            FOREIGN KEY (profile_id) REFERENCES language_profiles(id)
        );

        CREATE TABLE era_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            title TEXT,
            overview TEXT,
            legacy_impact TEXT,
            diagram TEXT
        );

        CREATE TABLE era_key_drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            era_id INTEGER NOT NULL,
            name TEXT,
            description TEXT,
            FOREIGN KEY (era_id) REFERENCES era_summaries(id)
        );

        CREATE TABLE era_pivotal_languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            era_id INTEGER NOT NULL,
            name TEXT,
            description TEXT,
            FOREIGN KEY (era_id) REFERENCES era_summaries(id)
        );

        CREATE TABLE concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            year INTEGER
        );

        CREATE TABLE concept_people (
            concept_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            PRIMARY KEY (concept_id, person_id),
            FOREIGN KEY (concept_id) REFERENCES concepts(id),
            FOREIGN KEY (person_id) REFERENCES people(id)
        );

        CREATE TABLE people_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL UNIQUE,
            title TEXT,
            overview TEXT,
            FOREIGN KEY (person_id) REFERENCES people(id)
        );

        CREATE TABLE people_profile_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            content TEXT,
            FOREIGN KEY (profile_id) REFERENCES people_profiles(id)
        );

        CREATE TABLE historical_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            title TEXT,
            date TEXT,
            overview TEXT
        );

        CREATE TABLE event_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            content TEXT,
            FOREIGN KEY (event_id) REFERENCES historical_events(id)
        );

        CREATE TABLE organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            founded TEXT
        );

        CREATE TABLE organization_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL UNIQUE,
            title TEXT,
            overview TEXT,
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        );

        CREATE TABLE organization_profile_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            content TEXT,
            FOREIGN KEY (profile_id) REFERENCES organization_profiles(id)
        );

        CREATE TABLE concept_bullets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL,
            name TEXT,
            description TEXT,
            FOREIGN KEY (concept_id) REFERENCES concepts(id)
        );

        CREATE TABLE concept_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL UNIQUE,
            title TEXT,
            overview TEXT,
            FOREIGN KEY (concept_id) REFERENCES concepts(id)
        );

        CREATE TABLE concept_profile_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            content TEXT,
            FOREIGN KEY (profile_id) REFERENCES concept_profiles(id)
        );

        CREATE TABLE crossroads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            explanation TEXT
        );

        CREATE TABLE modern_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme TEXT NOT NULL UNIQUE,
            explanation TEXT
        );

        CREATE TABLE paradigm_matrix_dimensions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            axis TEXT NOT NULL UNIQUE,
            details TEXT
        );

        CREATE TABLE timeline_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            era_or_period TEXT NOT NULL UNIQUE
        );

        CREATE TABLE timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_id INTEGER NOT NULL,
            year TEXT,
            description TEXT,
            FOREIGN KEY (period_id) REFERENCES timeline_periods(id)
        );

        CREATE TABLE timeline_event_related (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            related_name TEXT,
            FOREIGN KEY (event_id) REFERENCES timeline_events(id)
        );

        CREATE TABLE learning_paths (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            type TEXT DEFAULT 'path' -- 'path' or 'project'
        );

        CREATE TABLE learning_path_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path_id TEXT NOT NULL,
            language_name TEXT NOT NULL,
            milestone TEXT,
            rationale TEXT,
            challenge TEXT,
            step_order INTEGER,
            FOREIGN KEY (path_id) REFERENCES learning_paths(id)
        );

        CREATE VIRTUAL TABLE fts_languages USING fts5(
            name, 
            display_name, 
            year UNINDEXED, 
            description, 
            philosophy, 
            mental_model,
            language_id UNINDEXED,
            tokenize='porter'
        );

        CREATE VIRTUAL TABLE fts_profiles USING fts5(
            language_name,
            section_name, 
            content,
            language_id UNINDEXED,
            profile_id UNINDEXED,
            section_id UNINDEXED,
            tokenize='porter'
        );

        CREATE VIRTUAL TABLE fts_concept_profiles USING fts5(
            concept_name,
            section_name, 
            content,
            concept_id UNINDEXED,
            profile_id UNINDEXED,
            section_id UNINDEXED,
            tokenize='porter'
        );
        """)
        
        # 4. Insert Data
        print("Inserting data...")
        
        # Paradigms
        paradigm_map: Dict[str, int] = {} # name -> id
        for p in loader.paradigms:
            cursor.execute("INSERT INTO paradigms (name, description) VALUES (?, ?)", (p['name'], p.get('description')))
            if cursor.lastrowid is not None:
                paradigm_map[p['name']] = cursor.lastrowid
            
        # People
        people_map: Dict[str, int] = {} # name -> id
        for p in loader.people:
            if p['name'] not in people_map:
                cursor.execute("INSERT INTO people (name) VALUES (?)", (p['name'],))
                if cursor.lastrowid is not None:
                    people_map[p['name']] = cursor.lastrowid

        # Concepts (from data/concepts.json)
        print("Inserting base concepts...")
        for c in loader.concepts:
            cursor.execute("INSERT OR IGNORE INTO concepts (name, description, year) VALUES (?, ?, ?)", (c['name'], c.get('description'), c.get('year')))
            cursor.execute("SELECT id FROM concepts WHERE name = ?", (c['name'],))
            concept_row = cursor.fetchone()
            if concept_row:
                concept_id = concept_row[0]
                for person in c.get('responsible', []):
                    if person not in people_map:
                        cursor.execute("INSERT INTO people (name) VALUES (?)", (person,))
                        if cursor.lastrowid is not None:
                            people_map[person] = cursor.lastrowid
                    cursor.execute("INSERT OR IGNORE INTO concept_people (concept_id, person_id) VALUES (?, ?)", (concept_id, people_map[person]))
                
        # Languages
        lang_map: Dict[str, int] = {} # name -> id
        for lang in loader.languages:
            # Insert language
            cursor.execute("""
                INSERT INTO languages (
                    name, display_name, year, cluster, generation, 
                    philosophy, description, mental_model, complexity_bias, safety_model, 
                    typing_discipline, memory_management, is_keystone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lang['name'],
                lang.get('display_name'),
                lang.get('year'),
                lang.get('cluster'),
                lang.get('generation'),
                lang.get('philosophy'),
                lang.get('philosophy'), # description mapping
                lang.get('mental_model'),
                lang.get('complexity_bias'),
                lang.get('safety_model'),
                lang.get('typing_discipline'),
                lang.get('memory_management'),
                lang.get('is_keystone', False)
            ))
            if cursor.lastrowid is not None:
                lang_id = cursor.lastrowid
                lang_map[lang['name']] = lang_id
            
                # Paradigms for this language
                for p_name in lang.get('paradigms', []):
                    if p_name not in paradigm_map:
                        cursor.execute("INSERT INTO paradigms (name) VALUES (?)", (p_name,))
                        if cursor.lastrowid is not None:
                            paradigm_map[p_name] = cursor.lastrowid
                    cursor.execute("INSERT OR IGNORE INTO language_paradigms (language_id, paradigm_id) VALUES (?, ?)", 
                                (lang_id, paradigm_map[p_name]))
                    
                # Creators for this language
                for person_name in lang.get('creators', []):
                    if person_name not in people_map:
                        cursor.execute("INSERT INTO people (name) VALUES (?)", (person_name,))
                        if cursor.lastrowid is not None:
                            people_map[person_name] = cursor.lastrowid
                    cursor.execute("INSERT OR IGNORE INTO language_people (language_id, person_id, role) VALUES (?, ?, ?)", 
                                (lang_id, people_map[person_name], 'Creator'))

        # Influences
        all_influences: Set[Tuple[int, int]] = set()
        
        # From influences.json
        for inf in loader.influences:
            src_name = inf['from']
            tgt_name = inf['to']
            if src_name in lang_map and tgt_name in lang_map:
                all_influences.add((lang_map[src_name], lang_map[tgt_name]))
                
        # From languages.json
        for lang in loader.languages:
            if lang['name'] in lang_map:
                lang_id = lang_map[lang['name']]
                for other_name in lang.get('influenced_by', []):
                    if other_name in lang_map:
                        all_influences.add((lang_map[other_name], lang_id))
                for other_name in lang.get('influenced', []):
                    if other_name in lang_map:
                        all_influences.add((lang_id, lang_map[other_name]))

        for src_id, tgt_id in all_influences:
            cursor.execute("INSERT OR IGNORE INTO influences (source_id, target_id) VALUES (?, ?)", (src_id, tgt_id))

        # Calculate influence_score
        print("Calculating influence scores...")
        cursor.execute("""
            UPDATE languages 
            SET influence_score = (
                SELECT COUNT(*) FROM influences WHERE source_id = languages.id
            ) + (
                SELECT COUNT(*) FROM influences WHERE target_id = languages.id
            )
        """)

        # Language Profiles
        profiles = loader.get_language_profiles()
        for key, profile in profiles.items():
            lang_id_found: Optional[int] = None
            if key in lang_map:
                lang_id_found = lang_map[key]
            else:
                space_key = key.replace('_', ' ')
                if space_key in lang_map:
                    lang_id_found = lang_map[space_key]
            
            if lang_id_found:
                cursor.execute("INSERT INTO language_profiles (language_id, title, overview) VALUES (?, ?, ?)", 
                            (lang_id_found, profile.get('title'), profile.get('overview')))
                profile_id = cursor.lastrowid
                
                if profile_id is not None:
                    for sec_name, content in profile.items():
                        if sec_name in ['title', 'overview']:
                            continue
                        if isinstance(content, list):
                            content = "\n".join(content)
                        cursor.execute("INSERT INTO profile_sections (profile_id, section_name, content) VALUES (?, ?, ?)",
                                    (profile_id, sec_name, str(content)))

        # Concept Profiles
        concept_profiles = loader.get_concept_profiles()
        concept_id_map: Dict[str, int] = {} # name -> id
        cursor.execute("SELECT name, id FROM concepts")
        for name, cid in cursor.fetchall():
            concept_id_map[name] = cid

        for key, profile in concept_profiles.items():
            concept_id_found: Optional[int] = None
            space_key = key.replace('_', ' ')
            
            if key in concept_id_map:
                concept_id_found = concept_id_map[key]
            elif space_key in concept_id_map:
                concept_id_found = concept_id_map[space_key]
            else:
                title = profile.get('title', space_key)
                name_only = title.split(':')[0].strip()
                if name_only in concept_id_map:
                    concept_id_found = concept_id_map[name_only]
                else:
                    cursor.execute("INSERT INTO concepts (name, description) VALUES (?, ?)", 
                                (name_only, profile.get('overview', 'Detailed concept profile available.')))
                    if cursor.lastrowid is not None:
                        concept_id_found = cursor.lastrowid
                        concept_id_map[name_only] = concept_id_found
            
            if concept_id_found:
                cursor.execute("INSERT INTO concept_profiles (concept_id, title, overview) VALUES (?, ?, ?)", 
                            (concept_id_found, profile.get('title'), profile.get('overview')))
                profile_id = cursor.lastrowid
                
                if profile_id is not None:
                    for sec_name, content in profile.items():
                        if sec_name in ['title', 'overview']:
                            continue
                        if isinstance(content, list):
                            content = "\n".join(content)
                        cursor.execute("INSERT INTO concept_profile_sections (profile_id, section_name, content) VALUES (?, ?, ?)",
                                    (profile_id, sec_name, str(content)))

        # People Profiles
        people_profiles = loader.get_people_profiles()
        person_id_map: Dict[str, int] = {} # name -> id
        cursor.execute("SELECT name, id FROM people")
        for name, pid in cursor.fetchall():
            person_id_map[name] = pid

        for key, profile in people_profiles.items():
            person_id_found: Optional[int] = None
            space_key = key.replace('_', ' ')
            
            if key in person_id_map:
                person_id_found = person_id_map[key]
            elif space_key in person_id_map:
                person_id_found = person_id_map[space_key]
            else:
                title = profile.get('title', space_key)
                name_only = title.split(':')[0].strip()
                if name_only in person_id_map:
                    person_id_found = person_id_map[name_only]
                else:
                    cursor.execute("INSERT INTO people (name) VALUES (?)", (name_only,))
                    if cursor.lastrowid is not None:
                        person_id_found = cursor.lastrowid
                        person_id_map[name_only] = person_id_found
            
            if person_id_found:
                cursor.execute("INSERT INTO people_profiles (person_id, title, overview) VALUES (?, ?, ?)", 
                            (person_id_found, profile.get('title'), profile.get('overview')))
                profile_id = cursor.lastrowid
                
                if profile_id is not None:
                    for sec_name, content in profile.items():
                        if sec_name in ['title', 'overview']:
                            continue
                        if isinstance(content, list):
                            content = "\n".join(content)
                        cursor.execute("INSERT INTO people_profile_sections (profile_id, section_name, content) VALUES (?, ?, ?)",
                                    (profile_id, sec_name, str(content)))

        # Historical Events
        historical_events = loader.get_historical_events()
        for key, event in historical_events.items():
            slug = event.get('slug', key)
            cursor.execute("INSERT INTO historical_events (slug, title, date, overview) VALUES (?, ?, ?, ?)",
                        (slug, event.get('title'), event.get('date'), event.get('overview')))
            event_id = cursor.lastrowid
            
            if event_id is not None:
                for sec_name, content in event.items():
                    if sec_name in ['slug', 'title', 'date', 'overview']:
                        continue
                    if isinstance(content, list):
                        content = "\n".join(content)
                    cursor.execute("INSERT INTO event_sections (event_id, section_name, content) VALUES (?, ?, ?)",
                                (event_id, sec_name, str(content)))

        # Organization Profiles
        org_profiles = loader.get_org_profiles()
        org_id_map: Dict[str, int] = {} # name -> id
        cursor.execute("SELECT name, id FROM organizations")
        for name, oid in cursor.fetchall():
            org_id_map[name] = oid

        for key, profile in org_profiles.items():
            org_id_found: Optional[int] = None
            space_key = key.replace('_', ' ')
            
            if key in org_id_map:
                org_id_found = org_id_map[key]
            elif space_key in org_id_map:
                org_id_found = org_id_map[space_key]
            else:
                title = profile.get('title', space_key)
                name_only = title.split(':')[0].strip()
                if name_only in org_id_map:
                    org_id_found = org_id_map[name_only]
                else:
                    cursor.execute("INSERT INTO organizations (name, founded) VALUES (?, ?)", 
                                (name_only, profile.get('founded')))
                    if cursor.lastrowid is not None:
                        org_id_found = cursor.lastrowid
                        org_id_map[name_only] = org_id_found
            
            if org_id_found:
                cursor.execute("INSERT INTO organization_profiles (org_id, title, overview) VALUES (?, ?, ?)", 
                            (org_id_found, profile.get('title'), profile.get('overview')))
                profile_id = cursor.lastrowid
                
                if profile_id is not None:
                    for sec_name, content in profile.items():
                        if sec_name in ['title', 'overview', 'founded']:
                            continue
                        if isinstance(content, list):
                            content = "\n".join(content)
                        cursor.execute("INSERT INTO organization_profile_sections (profile_id, section_name, content) VALUES (?, ?, ?)",
                                    (profile_id, sec_name, str(content)))

        # 5. Populate FTS Tables
        
        # Era Summaries
        print("Inserting era summaries...")
        for era in loader.get_all_era_summaries():
            cursor.execute("INSERT INTO era_summaries (slug, title, overview, legacy_impact, diagram) VALUES (?, ?, ?, ?, ?)",
                (era.get('slug'), era.get('title'), era.get('overview'), era.get('legacy_impact'), era.get('diagram')))
            era_id = cursor.lastrowid

            if era_id is not None:
                for driver in era.get('key_drivers', []):
                    cursor.execute("INSERT INTO era_key_drivers (era_id, name, description) VALUES (?, ?, ?)",
                        (era_id, driver.get('name'), driver.get('description')))

                for lang in era.get('pivotal_languages', []):
                    cursor.execute("INSERT INTO era_pivotal_languages (era_id, name, description) VALUES (?, ?, ?)",
                        (era_id, lang.get('name'), lang.get('description')))

        # Concepts
        print("Inserting concepts reference...")
        concepts_ref = loader.get_concepts_reference()
        if concepts_ref:
            for concept in concepts_ref.get('concepts', []):
                cursor.execute("INSERT OR IGNORE INTO concepts (name, description) VALUES (?, ?)",
                            (concept.get('name'), concept.get('description')))
                cursor.execute("SELECT id FROM concepts WHERE name = ?", (concept.get('name'),))
                row_cid = cursor.fetchone()
                if row_cid:
                    concept_id = row_cid[0]
                    for bullet in concept.get('bullets', []):
                        cursor.execute("INSERT INTO concept_bullets (concept_id, name, description) VALUES (?, ?, ?)",
                                    (concept_id, bullet.get('name'), bullet.get('description')))

        # Crossroads
        print("Inserting crossroads...")
        crossroads_data = loader.get_crossroads()
        if isinstance(crossroads_data, list):
            for cr in crossroads_data:
                cursor.execute("INSERT OR IGNORE INTO crossroads (title, explanation) VALUES (?, ?)",
                            (cr.get('title'), cr.get('explanation')))

        # Modern Reactions
        print("Inserting modern reactions...")
        modern_reactions_data = loader.get_modern_reactions()
        if isinstance(modern_reactions_data, list):
            for mr in modern_reactions_data:
                cursor.execute("INSERT OR IGNORE INTO modern_reactions (theme, explanation) VALUES (?, ?)",
                            (mr.get('theme'), mr.get('explanation')))
        # Paradigm Matrix
        print("Inserting paradigm matrix...")
        matrix_data = loader.get_paradigm_matrix()
        if matrix_data:
            for dim in matrix_data.get('dimensions', []):
                cursor.execute("INSERT INTO paradigm_matrix_dimensions (axis, details) VALUES (?, ?)",
                            (dim.get('axis'), dim.get('details')))

        # Timeline
        print("Inserting timeline...")
        timeline_data = loader.get_timeline()
        if isinstance(timeline_data, list):
            for period in timeline_data:
                cursor.execute("INSERT INTO timeline_periods (era_or_period) VALUES (?)", (period.get('era_or_period'),))
                period_id = cursor.lastrowid
                
                if period_id is not None:
                    for event in period.get('events', []):
                        cursor.execute("INSERT INTO timeline_events (period_id, year, description) VALUES (?, ?, ?)",
                                    (period_id, event.get('year'), event.get('description')))
                        event_id = cursor.lastrowid
                        
                        if event_id is not None:
                            for related in event.get('related', []):
                                cursor.execute("INSERT INTO timeline_event_related (event_id, related_name) VALUES (?, ?)",
                                            (event_id, related))

        # Learning Paths
        print("Inserting learning paths...")
        learning_paths = loader.get_learning_paths()
        for path in learning_paths:
            cursor.execute("INSERT INTO learning_paths (id, title, description, type) VALUES (?, ?, ?, ?)",
                        (path['id'], path['title'], path['description'], path.get('type', 'path')))
            
            for idx, step in enumerate(path.get('steps', [])):
                cursor.execute("""
                    INSERT INTO learning_path_steps (path_id, language_name, milestone, rationale, challenge, step_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (path['id'], step['language'], step.get('milestone'), step.get('rationale'), step.get('challenge'), idx))

        print("Populating FTS tables...")

        cursor.execute("""
            INSERT INTO fts_languages (name, display_name, year, description, philosophy, mental_model, language_id)
            SELECT name, display_name, year, description, philosophy, mental_model, id
            FROM languages;
        """)
        
        cursor.execute("""
            INSERT INTO fts_profiles (language_name, section_name, content, language_id, profile_id, section_id)
            SELECT l.name, 'Overview', lp.overview, l.id, lp.id, NULL
            FROM languages l
            JOIN language_profiles lp ON l.id = lp.language_id
            WHERE lp.overview IS NOT NULL;
        """)
        
        cursor.execute("""
            INSERT INTO fts_profiles (language_name, section_name, content, language_id, profile_id, section_id)
            SELECT l.name, ps.section_name, ps.content, l.id, lp.id, ps.id
            FROM languages l
            JOIN language_profiles lp ON l.id = lp.language_id
            JOIN profile_sections ps ON lp.id = ps.profile_id;
        """)

        # Populate fts_concept_profiles
        cursor.execute("""
            INSERT INTO fts_concept_profiles (concept_name, section_name, content, concept_id, profile_id, section_id)
            SELECT c.name, 'Overview', cp.overview, c.id, cp.id, NULL
            FROM concepts c
            JOIN concept_profiles cp ON c.id = cp.concept_id
            WHERE cp.overview IS NOT NULL;
        """)
        
        cursor.execute("""
            INSERT INTO fts_concept_profiles (concept_name, section_name, content, concept_id, profile_id, section_id)
            SELECT c.name, cps.section_name, cps.content, c.id, cp.id, cps.id
            FROM concepts c
            JOIN concept_profiles cp ON c.id = cp.concept_id
            JOIN concept_profile_sections cps ON cp.id = cps.profile_id;
        """)

        # 6. Create Indexes
        print("Creating indexes...")
        cursor.executescript("""
        CREATE INDEX idx_influences_source ON influences(source_id);
        CREATE INDEX idx_influences_target ON influences(target_id);
        CREATE INDEX idx_lang_paradigms_lang ON language_paradigms(language_id);
        CREATE INDEX idx_lang_paradigms_paradigm ON language_paradigms(paradigm_id);
        CREATE INDEX idx_lang_people_lang ON language_people(language_id);
        CREATE INDEX idx_lang_people_person ON language_people(person_id);
        CREATE INDEX idx_profile_sections_profile ON profile_sections(profile_id);
        CREATE INDEX idx_concept_profile_sections_profile ON concept_profile_sections(profile_id);
        """)
        
        # 7. Create Views
        print("Creating views...")
        cursor.execute("""
        CREATE VIEW v_language_details AS
        SELECT 
            l.id,
            l.name,
            l.display_name,
            l.year,
            l.cluster,
            l.generation,
            l.influence_score,
            lp.title as profile_title,
            (SELECT GROUP_CONCAT(p.name, ', ') 
            FROM paradigms p 
            JOIN language_paradigms lpa ON p.id = lpa.paradigm_id 
            WHERE lpa.language_id = l.id) as paradigms,
            (SELECT GROUP_CONCAT(pe.name, ', ') 
            FROM people pe 
            JOIN language_people lpe ON pe.id = lpe.person_id 
            WHERE lpe.language_id = l.id) as creators
        FROM languages l
        LEFT JOIN language_profiles lp ON l.id = lp.language_id;
        """)

        # Unified search view for combined results
        cursor.execute("""
        CREATE VIEW v_global_search AS
        SELECT 
            'language' as category,
            language_id,
            name as title,
            description as snippet,
            'languages' as source_table
        FROM fts_languages
        UNION ALL
        SELECT
            'profile' as category,
            language_id,
            language_name || ' (' || section_name || ')' as title,
            content as snippet,
            'profile_sections' as source_table
        FROM fts_profiles
        UNION ALL
        SELECT
            'concept' as category,
            concept_id,
            concept_name || ' (' || section_name || ')' as title,
            content as snippet,
            'concept_profile_sections' as source_table
        FROM fts_concept_profiles;
        """)

        # Sync Triggers for fts_languages
        cursor.executescript("""
        CREATE TRIGGER languages_ai AFTER INSERT ON languages BEGIN
        INSERT INTO fts_languages(rowid, name, display_name, description, philosophy, mental_model, language_id)
        VALUES (new.id, new.name, new.display_name, new.description, new.philosophy, new.mental_model, new.id);
        END;
        CREATE TRIGGER languages_ad AFTER DELETE ON languages BEGIN
        DELETE FROM fts_languages WHERE rowid = old.id;
        END;
        CREATE TRIGGER languages_au AFTER UPDATE ON languages BEGIN
        DELETE FROM fts_languages WHERE rowid = old.id;
        INSERT INTO fts_languages(rowid, name, display_name, description, philosophy, mental_model, language_id)
        VALUES (new.id, new.name, new.display_name, new.description, new.philosophy, new.mental_model, new.id);
        END;
        """)
        
        conn.commit()
        print(f"Database built successfully at {DB_PATH}")
    finally:
        if close_conn and conn:
            conn.close()

if __name__ == "__main__":
    build_database()
