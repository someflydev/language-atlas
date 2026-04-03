#!/usr/bin/env python3
import sqlite3
import os
import sys

# Ensure we can import from src
# This script is in src/app/core/build_sqlite.py
# Root is 3 levels up
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(os.path.join(REPO_ROOT, 'src'))

from app.core.data_loader import DataLoader

DB_PATH = os.path.join(REPO_ROOT, 'language_atlas.sqlite')

def build_database():
    print(f"Loading data from JSON...")
    loader = DataLoader()
    
    # 2. Drop and recreate DB
    if os.path.exists(DB_PATH):
        print(f"Removing existing database at {DB_PATH}")
        os.remove(DB_PATH)
        
    print(f"Creating new database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
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
        is_keystone BOOLEAN
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

    -- Full-Text Search Tables
    -- fts_languages: Keyword search across core language metadata
    CREATE VIRTUAL TABLE fts_languages USING fts5(
        name, 
        display_name, 
        year UNINDEXED, 
        description, 
        philosophy, 
        mental_model,
        language_id UNINDEXED
    );

    -- fts_profiles: Deep search through narrative profile content and sections
    CREATE VIRTUAL TABLE fts_profiles USING fts5(
        language_name,
        section_name, 
        content,
        language_id UNINDEXED,
        profile_id UNINDEXED,
        section_id UNINDEXED
    );
    """)
    
    # 4. Insert Data
    print("Inserting data...")
    
    # Paradigms
    paradigm_map = {} # name -> id
    for p in loader.paradigms:
        cursor.execute("INSERT INTO paradigms (name, description) VALUES (?, ?)", (p['name'], p.get('description')))
        paradigm_map[p['name']] = cursor.lastrowid
        
    # People
    people_map = {} # name -> id
    for p in loader.people:
        if p['name'] not in people_map:
            cursor.execute("INSERT INTO people (name) VALUES (?)", (p['name'],))
            people_map[p['name']] = cursor.lastrowid
            
    # Languages
    lang_map = {} # name -> id
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
        lang_id = cursor.lastrowid
        lang_map[lang['name']] = lang_id
        
        # Paradigms for this language
        for p_name in lang.get('paradigms', []):
            if p_name not in paradigm_map:
                cursor.execute("INSERT INTO paradigms (name) VALUES (?)", (p_name,))
                paradigm_map[p_name] = cursor.lastrowid
            cursor.execute("INSERT OR IGNORE INTO language_paradigms (language_id, paradigm_id) VALUES (?, ?)", 
                           (lang_id, paradigm_map[p_name]))
            
        # Creators for this language
        for person_name in lang.get('creators', []):
            if person_name not in people_map:
                cursor.execute("INSERT INTO people (name) VALUES (?)", (person_name,))
                people_map[person_name] = cursor.lastrowid
            cursor.execute("INSERT OR IGNORE INTO language_people (language_id, person_id, role) VALUES (?, ?, ?)", 
                           (lang_id, people_map[person_name], 'Creator'))

    # Influences
    # Combine influences.json with influenced_by/influenced from languages.json
    all_influences = set()
    
    # From influences.json
    for inf in loader.influences:
        src_name = inf['from']
        tgt_name = inf['to']
        if src_name in lang_map and tgt_name in lang_map:
            all_influences.add((lang_map[src_name], lang_map[tgt_name]))
            
    # From languages.json
    for lang in loader.languages:
        lang_id = lang_map[lang['name']]
        for other_name in lang.get('influenced_by', []):
            if other_name in lang_map:
                all_influences.add((lang_map[other_name], lang_id))
        for other_name in lang.get('influenced', []):
            if other_name in lang_map:
                all_influences.add((lang_id, lang_map[other_name]))

    for src_id, tgt_id in all_influences:
        cursor.execute("INSERT OR IGNORE INTO influences (source_id, target_id) VALUES (?, ?)", (src_id, tgt_id))

    # Language Profiles
    profiles = loader.get_language_profiles()
    for key, profile in profiles.items():
        lang_id = None
        # key is filename without extension (e.g., "ALGOL_60", "Python", "C++")
        if key in lang_map:
            lang_id = lang_map[key]
        else:
            # Try to match by name normalization (underscore to space)
            space_key = key.replace('_', ' ')
            if space_key in lang_map:
                lang_id = lang_map[space_key]
        
        if lang_id:
            cursor.execute("INSERT INTO language_profiles (language_id, title, overview) VALUES (?, ?, ?)", 
                           (lang_id, profile.get('title'), profile.get('overview')))
            profile_id = cursor.lastrowid
            
            # Sections
            for sec_name, content in profile.items():
                if sec_name in ['title', 'overview']:
                    continue
                if isinstance(content, list):
                    content = "\n".join(content)
                cursor.execute("INSERT INTO profile_sections (profile_id, section_name, content) VALUES (?, ?, ?)",
                               (profile_id, sec_name, str(content)))

    # 5. Populate FTS Tables
    print("Populating FTS tables...")
    cursor.execute("""
        INSERT INTO fts_languages (name, display_name, year, description, philosophy, mental_model, language_id)
        SELECT name, display_name, year, description, philosophy, mental_model, id
        FROM languages;
    """)
    
    # Populate fts_profiles with both the top-level overview and individual sections
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

    # Unified search view for combined results across languages and profiles
    cursor.execute("""
    CREATE VIEW v_global_search AS
    SELECT 
        'language' as category,
        language_id as entity_id,
        name as title,
        description as snippet,
        'languages' as source_table
    FROM fts_languages
    UNION ALL
    SELECT
        'profile' as category,
        language_id as entity_id,
        language_name || ' - ' || section_name as title,
        content as snippet,
        'profile_sections' as source_table
    FROM fts_profiles;
    """)
    
    conn.commit()
    conn.close()
    print(f"Database built successfully at {DB_PATH}")

if __name__ == "__main__":
    build_database()
