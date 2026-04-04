import json
import os
import sqlite3

class DataLoader:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Assume we are in src/app/core/data_loader.py
            # Root is 3 levels up
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            self.data_dir = os.path.join(base_dir, 'data')
            self.db_path = os.path.join(base_dir, 'language_atlas.sqlite')
        else:
            self.data_dir = data_dir
            # For custom data_dir, we look for sqlite in the same parent if not specified
            self.db_path = os.path.join(os.path.dirname(data_dir), 'language_atlas.sqlite')

        self.use_sqlite = os.environ.get('USE_SQLITE') == '1' and os.path.exists(self.db_path)

        if not self.use_sqlite:
            self.languages = self._load_json('languages.json')
            self.paradigms = self._load_json('paradigms.json')
            self.eras = self._load_json('eras.json')
            self.concepts = self._load_json('concepts.json')
            self.influences = self._load_json('influences.json')
            self.people = self._load_json('people.json')
            self.language_profiles = self._load_language_profiles()
        else:
            # When using SQLite, we don't load all data into memory at once
            self.languages = []
            self.paradigms = []
            self.eras = []
            self.concepts = []
            self.influences = []
            self.people = []
            self.language_profiles = {}

    def _get_connection(self):
        """Returns a read-only connection to the SQLite database."""
        # Use uri=True for read-only access
        conn = sqlite3.connect(f'file:{self.db_path}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_json(self, filename):
        dataset_name = filename.replace('.json', '')
        result = None

        # 1. Try to load from <dataset>.json
        file_path = os.path.join(self.data_dir, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # 2. Try to load from <dataset>/ directory
        dir_path = os.path.join(self.data_dir, dataset_name)
        if os.path.isdir(dir_path):
            json_files = []
            for root, _, files in os.walk(dir_path):
                for f in files:
                    if f.endswith('.json'):
                        json_files.append(os.path.join(root, f))
            
            # Sort alphabetically by filename as requested
            json_files.sort(key=lambda x: os.path.basename(x))
            
            for f_path in json_files:
                try:
                    with open(f_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if result is None:
                            result = data
                        else:
                            result = self._merge_data(result, data)
                except (json.JSONDecodeError, IOError):
                    continue

        return result if result is not None else []

    def _load_language_profiles(self):
        """
        Loads extended language profile JSON files from data/docs/language_profiles/
        Returns a dictionary mapping normalized language names to their profile data.
        """
        profiles_dir = os.path.join(self.data_dir, 'docs', 'language_profiles')
        profiles = {}
        
        if not os.path.isdir(profiles_dir):
            return profiles

        for filename in os.listdir(profiles_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(profiles_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Use filename without extension as the key
                        key = filename[:-5]
                        profiles[key] = data
                except (json.JSONDecodeError, IOError):
                    continue
        
        return profiles

    def _merge_data(self, base, new_data):
        if isinstance(base, list) and isinstance(new_data, list):
            base.extend(new_data)
        elif isinstance(base, dict) and isinstance(new_data, dict):
            base.update(new_data)
        return base


    def get_all_era_summaries(self):
        dir_path = os.path.join(self.data_dir, 'docs', 'era_summaries')
        summaries = []
        if os.path.isdir(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith('.json'):
                    with open(os.path.join(dir_path, filename), 'r', encoding='utf-8') as f:
                        summaries.append(json.load(f))
        return summaries

    def get_era_summary(self, slug):
        summaries = self.get_all_era_summaries()
        for s in summaries:
            if s.get('slug') == slug:
                return s
        return None

    def get_concepts_reference(self):
        return self._load_json('docs/concepts/concepts_reference.json')

    def get_crossroads(self):
        return self._load_json('docs/crossroads/crossroads.json')

    def get_modern_reactions(self):
        return self._load_json('docs/modern_reactions/modern_reactions.json')

    def get_paradigms_reference(self):
        return self._load_json('docs/paradigms/paradigms_reference.json')

    def get_paradigm_matrix(self):
        return self._load_json('docs/paradigms/paradigm_matrix.json')

    def get_timeline(self):
        return self._load_json('docs/timeline/timeline.json')

    def get_all_languages(self, filter_gen=None, filter_cluster=None):
        if not self.use_sqlite:
            langs = self.languages
            if filter_gen:
                langs = [l for l in langs if l.get('generation', '').lower() == filter_gen.lower()]
            if filter_cluster:
                langs = [l for l in langs if l.get('cluster', '').lower() == filter_cluster.lower()]
            return langs
        
        conn = self._get_connection()
        query = "SELECT * FROM languages WHERE 1=1"
        params = []
        if filter_gen:
            query += " AND lower(generation) = ?"
            params.append(filter_gen.lower())
        if filter_cluster:
            query += " AND lower(cluster) = ?"
            params.append(filter_cluster.lower())
        
        cursor = conn.execute(query, params)
        langs = [self._row_to_dict(row) for row in cursor.fetchall()]
        
        # Hydrate languages with paradigms and creators if needed
        for lang in langs:
            self._hydrate_language_json_compatibility(lang, conn)
        
        conn.close()
        return langs

    def _row_to_dict(self, row):
        """Converts an sqlite3.Row to a dictionary."""
        d = dict(row)
        # Convert sqlite booleans to python booleans
        for k, v in d.items():
            if v == 1 and k.startswith('is_'):
                d[k] = True
            elif v == 0 and k.startswith('is_'):
                d[k] = False
        return d

    def _hydrate_language_json_compatibility(self, lang, conn):
        """Adds paradigms, creators, etc. to match the JSON format."""
        lang_id = lang['id']
        
        # Paradigms
        cursor = conn.execute("""
            SELECT p.name 
            FROM paradigms p 
            JOIN language_paradigms lp ON p.id = lp.paradigm_id 
            WHERE lp.language_id = ?
        """, (lang_id,))
        lang['paradigms'] = [r['name'] for r in cursor.fetchall()]
        
        # Creators (People)
        cursor = conn.execute("""
            SELECT p.name 
            FROM people p 
            JOIN language_people lp ON p.id = lp.person_id 
            WHERE lp.language_id = ?
        """, (lang_id,))
        lang['creators'] = [r['name'] for r in cursor.fetchall()]

        # Influences
        cursor = conn.execute("""
            SELECT l.name 
            FROM languages l 
            JOIN influences i ON l.id = i.source_id 
            WHERE i.target_id = ?
        """, (lang_id,))
        lang['influenced_by'] = [r['name'] for r in cursor.fetchall()]
        
        cursor = conn.execute("""
            SELECT l.name 
            FROM languages l 
            JOIN influences i ON l.id = i.target_id 
            WHERE i.source_id = ?
        """, (lang_id,))
        lang['influenced'] = [r['name'] for r in cursor.fetchall()]

        # Primary Use Cases & Key Innovations (from profile sections if available)
        cursor = conn.execute("""
            SELECT ps.section_name, ps.content 
            FROM profile_sections ps 
            JOIN language_profiles lp ON ps.profile_id = lp.id 
            WHERE lp.language_id = ? AND ps.section_name IN ('primary_use_cases', 'key_innovations')
        """, (lang_id,))
        for row in cursor.fetchall():
            section = row['section_name']
            content = row['content']
            if content:
                # If it's a list stored as newline-separated string
                lang[section] = content.split('\n')
            else:
                lang[section] = []
        
        # Ensure they exist even if empty
        if 'primary_use_cases' not in lang: lang['primary_use_cases'] = []
        if 'key_innovations' not in lang: lang['key_innovations'] = []

    def get_language(self, name):
        if not self.use_sqlite:
            for lang in self.languages:
                if lang['name'].lower() == name.lower():
                    return lang
            return None
        
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM languages WHERE lower(name) = ?", (name.lower(),))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        lang = self._row_to_dict(row)
        self._hydrate_language_json_compatibility(lang, conn)
        conn.close()
        return lang

    def get_language_profiles(self):
        """Returns all loaded language profile data."""
        if not self.use_sqlite:
            return self.language_profiles
            
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT l.name, lp.* 
            FROM languages l 
            JOIN language_profiles lp ON l.id = lp.language_id
        """)
        profiles = {}
        for row in cursor.fetchall():
            lang_name = row['name']
            profile_id = row['id']
            profile_data = self._row_to_dict(row)
            
            # Fetch sections
            s_cursor = conn.execute("SELECT section_name, content FROM profile_sections WHERE profile_id = ?", (profile_id,))
            for s_row in s_cursor.fetchall():
                profile_data[s_row['section_name']] = s_row['content']
            
            profiles[lang_name] = profile_data
        
        conn.close()
        return profiles

    def get_language_profile(self, name):
        """
        Returns the profile data for a given language name.
        """
        if not self.use_sqlite:
            # 1. Try direct match
            if name in self.language_profiles:
                return self.language_profiles[name]
            
            # 2. Try normalized match (space -> underscore)
            normalized_name = name.replace(' ', '_')
            if normalized_name in self.language_profiles:
                return self.language_profiles[normalized_name]
            return None

        conn = self._get_connection()
        # Try both direct and normalized names in SQL
        normalized_name = name.replace(' ', '_')
        cursor = conn.execute("""
            SELECT lp.* 
            FROM language_profiles lp 
            JOIN languages l ON l.id = lp.language_id 
            WHERE lower(l.name) = ? OR lower(l.name) = ?
        """, (name.lower(), normalized_name.lower()))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        profile_id = row['id']
        profile_data = self._row_to_dict(row)
        
        # Fetch sections
        s_cursor = conn.execute("SELECT section_name, content FROM profile_sections WHERE profile_id = ?", (profile_id,))
        for s_row in s_cursor.fetchall():
            profile_data[s_row['section_name']] = s_row['content']
            
        conn.close()
        return profile_data

    def get_combined_language_data(self, name):
        """
        Returns a dictionary merging core language data with its extended profile.
        """
        lang = self.get_language(name)
        if not lang:
            return None
        
        # Create a copy to avoid mutating the original core data
        combined = dict(lang)
        
        profile = self.get_language_profile(lang['name'])
        if profile:
            combined.update(profile)
            
        return combined

    def get_influences(self, name):
        lang = self.get_language(name)
        if not lang:
            return None
        return {
            'influenced_by': lang.get('influenced_by', []),
            'influenced': lang.get('influenced', [])
        }

    def get_all_eras(self):
        if not self.use_sqlite:
            return self.eras
            
        # eras.json is not currently in SQLite schema based on build_sqlite.py
        # but the prompt says query SQLite directly instead of loading all JSON.
        # If it's not in SQLite, I should probably still load it from JSON if needed,
        # but for now I'll check if build_sqlite.py added it.
        # It didn't. I'll stick to JSON for eras for now, or just return empty if preferred.
        # Actually, let's keep JSON for what's not in SQLite to avoid breaking things.
        if not hasattr(self, '_eras_cache') or self._eras_cache is None:
            self._eras_cache = self._load_json('eras.json')
        return self._eras_cache

    def get_all_people(self):
        if not self.use_sqlite:
            return self.people
            
        conn = self._get_connection()
        cursor = conn.execute("SELECT name FROM people ORDER BY name")
        people = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        return people

    def get_all_influences(self):
        if not self.use_sqlite:
            return self.influences
            
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT l1.name as 'from', l2.name as 'to'
            FROM influences i
            JOIN languages l1 ON i.source_id = l1.id
            JOIN languages l2 ON i.target_id = l2.id
        """)
        influences = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        return influences

    def get_all_clusters(self):
        if not self.use_sqlite:
            clusters = set()
            for lang in self.languages:
                if 'cluster' in lang:
                    clusters.add(lang['cluster'])
            return sorted(list(clusters))
            
        conn = self._get_connection()
        cursor = conn.execute("SELECT DISTINCT cluster FROM languages WHERE cluster IS NOT NULL ORDER BY cluster")
        clusters = [row['cluster'] for row in cursor.fetchall()]
        conn.close()
        return clusters

    def get_all_paradigms(self):
        if not self.use_sqlite:
            paradigms = set()
            for lang in self.languages:
                if 'paradigms' in lang:
                    for p in lang['paradigms']:
                        paradigms.add(p)
            return sorted(list(paradigms))
            
        conn = self._get_connection()
        cursor = conn.execute("SELECT name FROM paradigms ORDER BY name")
        paradigms = [row['name'] for row in cursor.fetchall()]
        conn.close()
        return paradigms

    def get_paradigm_info(self, name):
        if not self.use_sqlite:
            for p in self.paradigms:
                if p['name'].lower() == name.lower():
                    return p
            return {"name": name, "description": "A core model or style of computer programming."}
            
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM paradigms WHERE lower(name) = ?", (name.lower(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_dict(row)
        return {"name": name, "description": "A core model or style of computer programming."}

    def search(self, term):
        """Performs a full-text search using FTS5 tables."""
        if not self.use_sqlite:
            # Simple in-memory search fallback
            results = []
            term = term.lower()
            for lang in self.get_all_languages():
                if term in lang['name'].lower() or term in lang.get('philosophy', '').lower():
                    results.append({
                        'category': 'language',
                        'title': lang['name'],
                        'snippet': lang.get('philosophy', '')[:200]
                    })
            return results

        conn = self._get_connection()
        # Search using the v_global_search view which combines fts_languages and fts_profiles
        # We need to join back to FTS tables if we want rank/snippets, 
        # but for now we'll do a simple match on the view if possible, 
        # or better, query the FTS tables directly.
        
        query = """
            SELECT 'language' as category, name as title, philosophy as snippet, rank
            FROM fts_languages 
            WHERE fts_languages MATCH ?
            UNION ALL
            SELECT 'profile' as category, language_name || ' - ' || section_name as title, content as snippet, rank
            FROM fts_profiles
            WHERE fts_profiles MATCH ?
            ORDER BY rank
            LIMIT 20
        """
        cursor = conn.execute(query, (term, term))
        results = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_cluster_info(self, name):
        # We don't have a cluster.json, so we provide generic info
        cluster_map = {
            "scientific": "Languages designed for numerical computation, physics simulations, and mathematical analysis.",
            "systems": "Low-level languages focused on memory management, hardware control, and performance.",
            "business": "Languages optimized for data processing, financial records, and enterprise administration.",
            "ai": "Languages designed for symbolic manipulation, logic, and artificial intelligence development.",
            "web": "Languages that power the internet, focusing on both client-side interactivity and server-side logic.",
            "cloud": "Modern languages designed for high concurrency, microservices, and distributed systems.",
            "scripting": "High-level languages used for automation, rapid prototyping, and glue-code.",
            "frontend": "Languages specifically designed to build interactive user interfaces in browsers.",
            "backend": "Languages optimized for server-side logic, databases, and API development."
        }
        desc = cluster_map.get(name.lower(), f"A functional grouping of languages with similar {name} goals.")
        return {"name": name, "description": desc}
