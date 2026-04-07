import json
import os
import sqlite3
from typing import List, Optional, Dict, Any, Union, Set, Tuple, cast

class DataLoader:
    def __init__(self, data_dir: Optional[str] = None) -> None:
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
            self.languages: List[Dict[str, Any]] = self._load_json('languages.json')
            self.paradigms: List[Dict[str, Any]] = self._load_json('paradigms.json')
            self.eras: List[Dict[str, Any]] = self._load_json('eras.json')
            self.concepts: List[Dict[str, Any]] = self._load_json('concepts.json')
            self.influences: List[Dict[str, Any]] = self._load_json('influences.json')
            self.people: List[Dict[str, Any]] = self._load_json('people.json')
            self.learning_paths: List[Dict[str, Any]] = self._load_json('learning_paths.json')
            self.language_profiles: Dict[str, Any] = self._load_language_profiles()
            self.concept_profiles: Dict[str, Any] = self._load_concept_profiles()
            self.people_profiles: Dict[str, Any] = self._load_people_profiles()
            self.historical_events: Dict[str, Any] = self._load_historical_events()
            self.org_profiles: Dict[str, Any] = self._load_org_profiles()
        else:
            # When using SQLite, we don't load all data into memory at once
            self.languages = []
            self.paradigms = []
            self.eras = []
            self.concepts = []
            self.influences = []
            self.people = []
            self.learning_paths = self._load_json('learning_paths.json')
            self.language_profiles = {}
            self.concept_profiles = {}
            self.people_profiles = {}
            self.historical_events = {}
            self.org_profiles = {}

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a read-only connection to the SQLite database."""
        # Use uri=True for read-only access
        conn = sqlite3.connect(f'file:{self.db_path}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_json(self, filename: str) -> List[Dict[str, Any]]:
        dataset_name = filename.replace('.json', '')
        result: Optional[List[Dict[str, Any]]] = None

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

        return cast(List[Dict[str, Any]], result if result is not None else [])

    def _load_language_profiles(self) -> Dict[str, Any]:
        """
        Loads extended language profile JSON files from data/docs/language_profiles/
        Returns a dictionary mapping normalized language names to their profile data.
        """
        profiles_dir = os.path.join(self.data_dir, 'docs', 'language_profiles')
        profiles: Dict[str, Any] = {}

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

    def _load_concept_profiles(self) -> Dict[str, Any]:
        """
        Loads extended concept profile JSON files from data/docs/concept_profiles/
        Returns a dictionary mapping normalized concept names to their profile data.
        """
        profiles_dir = os.path.join(self.data_dir, 'docs', 'concept_profiles')
        profiles: Dict[str, Any] = {}

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

    def _load_people_profiles(self) -> Dict[str, Any]:
        profiles_dir = os.path.join(self.data_dir, 'docs', 'people_profiles')
        profiles: Dict[str, Any] = {}
        if not os.path.isdir(profiles_dir): return profiles
        for filename in os.listdir(profiles_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(profiles_dir, filename), 'r', encoding='utf-8') as f:
                        profiles[filename[:-5]] = json.load(f)
                except (json.JSONDecodeError, IOError): continue
        return profiles

    def get_people_profiles(self) -> Dict[str, Any]:
        if not self.use_sqlite:
            return getattr(self, 'people_profiles', {})

        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT p.name, pp.* 
                FROM people p 
                JOIN people_profiles pp ON p.id = pp.person_id
            """)
            profiles = {}
            for row in cursor.fetchall():
                person_name = row['name']
                profile_id = row['id']
                profile_data = self._row_to_dict(row)

                s_cursor = conn.execute("SELECT section_name, content FROM people_profile_sections WHERE profile_id = ?", (profile_id,))
                for s_row in s_cursor.fetchall():
                    profile_data[s_row['section_name']] = s_row['content']

                profiles[person_name] = profile_data
            return profiles
        finally:
            conn.close()

    def _load_historical_events(self) -> Dict[str, Any]:
        events_dir = os.path.join(self.data_dir, 'docs', 'historical_events')
        events: Dict[str, Any] = {}
        if not os.path.isdir(events_dir): return events
        for filename in os.listdir(events_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(events_dir, filename), 'r', encoding='utf-8') as f:
                        events[filename[:-5]] = json.load(f)
                except (json.JSONDecodeError, IOError): continue
        return events

    def get_historical_events(self) -> Dict[str, Any]:
        if not self.use_sqlite:
            return getattr(self, 'historical_events', {})

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM historical_events")
            events = {}
            for row in cursor.fetchall():
                event_slug = row['slug']
                event_id = row['id']
                event_data = self._row_to_dict(row)

                s_cursor = conn.execute("SELECT section_name, content FROM event_sections WHERE event_id = ?", (event_id,))
                for s_row in s_cursor.fetchall():
                    event_data[s_row['section_name']] = s_row['content']

                events[event_slug] = event_data
            return events
        finally:
            conn.close()

    def _load_org_profiles(self) -> Dict[str, Any]:
        profiles_dir = os.path.join(self.data_dir, 'docs', 'org_profiles')
        profiles: Dict[str, Any] = {}
        if not os.path.isdir(profiles_dir): return profiles
        for filename in os.listdir(profiles_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(profiles_dir, filename), 'r', encoding='utf-8') as f:
                        profiles[filename[:-5]] = json.load(f)
                except (json.JSONDecodeError, IOError): continue
        return profiles

    def get_org_profiles(self) -> Dict[str, Any]:
        if not self.use_sqlite:
            return getattr(self, 'org_profiles', {})

        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT o.name, op.* 
                FROM organizations o 
                JOIN organization_profiles op ON o.id = op.org_id
            """)
            profiles = {}
            for row in cursor.fetchall():
                org_name = row['name']
                profile_id = row['id']
                profile_data = self._row_to_dict(row)

                s_cursor = conn.execute("SELECT section_name, content FROM organization_profile_sections WHERE profile_id = ?", (profile_id,))
                for s_row in s_cursor.fetchall():
                    profile_data[s_row['section_name']] = s_row['content']

                profiles[org_name] = profile_data
            return profiles
        finally:
            conn.close()

    def get_org(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns the profile data for a given organization name."""
        if not self.use_sqlite:
            profiles = self.get_org_profiles()
            if name in profiles: return profiles[name]
            norm_name = name.replace(' ', '_')
            if norm_name in profiles: return profiles[norm_name]
            return None

        conn = self._get_connection()
        try:
            alt_name = name.replace('_', ' ')
            cursor = conn.execute("""
                SELECT op.*, o.name 
                FROM organization_profiles op 
                JOIN organizations o ON o.id = op.org_id 
                WHERE lower(o.name) = ? OR lower(o.name) = ?
            """, (name.lower(), alt_name.lower()))

            row = cursor.fetchone()
            if not row:
                return None

            profile_id = row['id']
            profile_data = self._row_to_dict(row)

            s_cursor = conn.execute("SELECT section_name, content FROM organization_profile_sections WHERE profile_id = ?", (profile_id,))
            for s_row in s_cursor.fetchall():
                profile_data[s_row['section_name']] = s_row['content']

            return profile_data
        finally:
            conn.close()

    def get_person(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns the profile data for a given person name."""
        if not self.use_sqlite:
            profiles = self.get_people_profiles()
            if name in profiles: return profiles[name]
            alt_name = name.replace('_', ' ')
            if alt_name in profiles: return profiles[alt_name]
            return None

        conn = self._get_connection()
        try:
            alt_name = name.replace('_', ' ')
            cursor = conn.execute("""
                SELECT pp.*, p.name 
                FROM people_profiles pp 
                JOIN people p ON p.id = pp.person_id 
                WHERE lower(p.name) = ? OR lower(p.name) = ?
            """, (name.lower(), alt_name.lower()))

            row = cursor.fetchone()
            if not row:
                return None

            profile_id = row['id']
            profile_data = self._row_to_dict(row)

            s_cursor = conn.execute("SELECT section_name, content FROM people_profile_sections WHERE profile_id = ?", (profile_id,))
            for s_row in s_cursor.fetchall():
                profile_data[s_row['section_name']] = s_row['content']

            return profile_data
        finally:
            conn.close()

    def get_event(self, slug: str) -> Optional[Dict[str, Any]]:
        """Returns the data for a given event slug."""
        if not self.use_sqlite:
            events = self.get_historical_events()
            if slug in events: return events[slug]
            for k, v in events.items():
                if v.get('slug') == slug: return v
            return None

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM historical_events WHERE slug = ? OR lower(title) = ?", (slug, slug.lower()))
            row = cursor.fetchone()
            if not row:
                return None

            event_id = row['id']
            event_data = self._row_to_dict(row)

            s_cursor = conn.execute("SELECT section_name, content FROM event_sections WHERE event_id = ?", (event_id,))
            for s_row in s_cursor.fetchall():
                event_data[s_row['section_name']] = s_row['content']

            return event_data
        finally:
            conn.close()

    def get_entity_link_map(self) -> Dict[str, str]:
        """Returns a map of entity names to their routes for auto-linking."""
        conn = self._get_connection()
        link_map: Dict[str, str] = {}
        try:
            # 1. Languages
            cursor = conn.execute("SELECT name, display_name FROM languages")
            for row in cursor.fetchall():
                link_map[row['name']] = f"/language/{row['name']}"
                if row['display_name'] and row['display_name'] != row['name']:
                    link_map[row['display_name']] = f"/language/{row['name']}"

            # 2. People
            cursor = conn.execute("SELECT name FROM people")
            for row in cursor.fetchall():
                name = row['name']
                link_map[name] = f"/person/{name.replace(' ', '_')}"

            # 3. Concepts
            cursor = conn.execute("SELECT name FROM concepts")
            for row in cursor.fetchall():
                name = row['name']
                link_map[name] = f"/concept/{name.replace(' ', '_')}"

            # 4. Organizations
            cursor = conn.execute("SELECT name FROM organizations")
            for row in cursor.fetchall():
                name = row['name']
                link_map[name] = f"/org/{name.replace(' ', '_')}"

            # 5. Events
            cursor = conn.execute("SELECT title, slug FROM historical_events")
            for row in cursor.fetchall():
                link_map[row['title']] = f"/event/{row['slug']}"

            return link_map
        finally:
            conn.close()

    def get_timeline_data(self) -> List[Dict[str, Any]]:
        """Fetches data for timeline visualization."""
        if not self.use_sqlite:
            return [{
                'name': l['name'],
                'year': l.get('year'),
                'cluster': l.get('cluster'),
                'influence_score': len(l.get('influenced_by', [])) + len(l.get('influenced', []))
            } for l in self.languages]

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT name, year, cluster, influence_score FROM languages WHERE year IS NOT NULL")
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_influence_data(self) -> List[Dict[str, str]]:
        """Fetches data for influence network visualization."""
        if not self.use_sqlite:
            edges = []
            for l in self.languages:
                for target in l.get('influenced', []):
                    edges.append({'source': l['name'], 'target': target})
            return edges

        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT s.name as source, t.name as target 
                FROM influences i
                JOIN languages s ON i.source_id = s.id
                JOIN languages t ON i.target_id = t.id
            """)
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _merge_data(self, base: Union[List[Any], Dict[str, Any]], new_data: Union[List[Any], Dict[str, Any]]) -> Union[List[Any], Dict[str, Any]]:
        if isinstance(base, list) and isinstance(new_data, list):
            base.extend(new_data)
        elif isinstance(base, dict) and isinstance(new_data, dict):
            base.update(new_data)
        return base

    def get_crossroads(self) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            data = self._load_json('docs/crossroads/crossroads.json')
            return cast(List[Dict[str, Any]], data.get('crossroads', []) if isinstance(data, dict) else data)

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM crossroads ORDER BY id")
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_modern_reactions(self) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            data = self._load_json('docs/modern_reactions/modern_reactions.json')
            return cast(List[Dict[str, Any]], data.get('reactions', []) if isinstance(data, dict) else data)

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM modern_reactions ORDER BY id")
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_all_era_summaries(self) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            dir_path = os.path.join(self.data_dir, 'docs', 'era_summaries')
            summaries = []
            if os.path.isdir(dir_path):
                for filename in os.listdir(dir_path):
                    if filename.endswith('.json'):
                        with open(os.path.join(dir_path, filename), 'r', encoding='utf-8') as f:
                            summaries.append(json.load(f))
            return summaries

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM era_summaries ORDER BY id")
            summaries = [self._row_to_dict(row) for row in cursor.fetchall()]

            for s in summaries:
                self._hydrate_era_summary(s, conn)
            return summaries
        finally:
            conn.close()

    def get_era_summary(self, slug: str) -> Optional[Dict[str, Any]]:
        if not self.use_sqlite:
            summaries = self.get_all_era_summaries()
            for s in summaries:
                if s.get('slug') == slug:
                    return s
            return None

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM era_summaries WHERE slug = ?", (slug,))
            row = cursor.fetchone()
            if not row:
                return None

            summary = self._row_to_dict(row)
            self._hydrate_era_summary(summary, conn)
            return summary
        finally:
            conn.close()

    def _hydrate_era_summary(self, summary: Dict[str, Any], conn: sqlite3.Connection) -> None:
        era_id = summary['id']

        # Key Drivers
        cursor = conn.execute("SELECT name, description FROM era_key_drivers WHERE era_id = ?", (era_id,))
        summary['key_drivers'] = [self._row_to_dict(r) for r in cursor.fetchall()]

        # Pivotal Languages
        cursor = conn.execute("SELECT name, description FROM era_pivotal_languages WHERE era_id = ?", (era_id,))
        summary['pivotal_languages'] = [self._row_to_dict(r) for r in cursor.fetchall()]

    def get_timeline(self) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            data = self._load_json('docs/timeline/timeline.json')
            return cast(List[Dict[str, Any]], data.get('periods', []) if isinstance(data, dict) else data)

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM timeline_periods ORDER BY id")
            periods = [self._row_to_dict(row) for row in cursor.fetchall()]

            for p in periods:
                p_id = p['id']
                e_cursor = conn.execute("SELECT year, description FROM timeline_events WHERE period_id = ? ORDER BY id", (p_id,))
                p['events'] = [self._row_to_dict(r) for r in e_cursor.fetchall()]
            return periods
        finally:
            conn.close()

    def get_all_concepts(self) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            return self.concepts

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM concepts ORDER BY year, name")
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_all_languages(self, clusters: Optional[List[str]] = None, paradigms: Optional[List[str]] = None, min_year: int = 1930, max_year: int = 2024, sort: str = "year", filter_gen: Optional[str] = None, filter_cluster: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            langs = list(self.languages)
            if filter_gen:
                langs = [l for l in langs if l.get('generation', '').lower() == filter_gen.lower()]
            if filter_cluster:
                langs = [l for l in langs if l.get('cluster', '').lower() == filter_cluster.lower()]
            if clusters:
                langs = [l for l in langs if l.get('cluster') in clusters]
            if paradigms:
                langs = [
                    l for l in langs 
                    if any(p in (l.get('paradigms') or []) for p in paradigms)
                ]
            langs = [l for l in langs if min_year <= l.get('year', 0) <= max_year]
            if sort == "name":
                langs.sort(key=lambda x: x['name'].lower())
            else:
                langs.sort(key=lambda x: x.get('year', 0))
            return langs

        conn = self._get_connection()
        try:
            query = "SELECT * FROM languages WHERE year BETWEEN ? AND ?"
            params: List[Any] = [min_year, max_year]

            if filter_gen:
                query += " AND lower(generation) = ?"
                params.append(filter_gen.lower())
            if filter_cluster:
                query += " AND lower(cluster) = ?"
                params.append(filter_cluster.lower())
            if clusters:
                placeholders = ', '.join(['?'] * len(clusters))
                query += f" AND cluster IN ({placeholders})"
                params.extend(clusters)
            if paradigms:
                placeholders = ', '.join(['?'] * len(paradigms))
                query += f""" AND id IN (
                    SELECT language_id FROM language_paradigms lp
                    JOIN paradigms p ON lp.paradigm_id = p.id
                    WHERE p.name IN ({placeholders})
                )"""
                params.extend(paradigms)

            if sort == "name":
                query += " ORDER BY lower(name) ASC"
            else:
                query += " ORDER BY year ASC"

            cursor = conn.execute(query, params)
            langs = [self._row_to_dict(row) for row in cursor.fetchall()]

            # Hydrate languages with paradigms and creators if needed
            for lang in langs:
                self._hydrate_language_json_compatibility(lang, conn)

            return langs
        finally:
            conn.close()

    def get_comparison_data(self, lang_names: List[str]) -> List[Dict[str, Any]]:
        """Fetches detailed data for multiple languages for side-by-side comparison."""
        if not self.use_sqlite:
            return [cast(Dict[str, Any], self.get_combined_language_data(name)) for name in lang_names if self.get_combined_language_data(name)]

        conn = self._get_connection()
        try:
            placeholders = ', '.join(['?'] * len(lang_names))
            # Match against either internal name or display name
            query = f"SELECT * FROM languages WHERE name IN ({placeholders}) OR display_name IN ({placeholders})"
            params = list(lang_names) + list(lang_names)

            cursor = conn.execute(query, params)
            langs = [self._row_to_dict(row) for row in cursor.fetchall()]

            for lang in langs:
                self._hydrate_language_json_compatibility(lang, conn)

            # Sort results to match requested order
            sorted_langs = []
            for name in lang_names:
                for lang in langs:
                    if lang['name'].lower() == name.lower() or lang['display_name'].lower() == name.lower():
                        sorted_langs.append(lang)
                        break
            return sorted_langs
        finally:
            conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Converts an sqlite3.Row to a dictionary."""
        d = dict(row)
        # Convert sqlite booleans to python booleans
        for k, v in d.items():
            if v == 1 and k.startswith('is_'):
                d[k] = True
            elif v == 0 and k.startswith('is_'):
                d[k] = False
        return d

    def _hydrate_language_json_compatibility(self, lang: Dict[str, Any], conn: sqlite3.Connection) -> None:
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

    def get_language(self, name: str) -> Optional[Dict[str, Any]]:
        if not self.use_sqlite:
            for lang in self.languages:
                if lang['name'].lower() == name.lower():
                    return lang
            return None

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM languages WHERE lower(name) = ?", (name.lower(),))
            row = cursor.fetchone()
            if not row:
                return None

            lang = self._row_to_dict(row)
            self._hydrate_language_json_compatibility(lang, conn)
            return lang
        finally:
            conn.close()

    def get_language_profiles(self) -> Dict[str, Any]:
        """Returns all loaded language profile data."""
        if not self.use_sqlite:
            return self.language_profiles

        conn = self._get_connection()
        try:
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
            return profiles
        finally:
            conn.close()

    def get_language_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Returns the profile data for a given language name.
        """
        if not self.use_sqlite:
            # 1. Try direct match
            if name in self.language_profiles:
                return self.language_profiles[name]

            # 2. Try normalized match (underscore -> space)
            alt_name = name.replace('_', ' ')
            if alt_name in self.language_profiles:
                return self.language_profiles[alt_name]
            return None

        conn = self._get_connection()
        try:
            # Try both direct and alternative names in SQL
            alt_name = name.replace('_', ' ')
            cursor = conn.execute("""
                SELECT lp.* 
                FROM language_profiles lp 
                JOIN languages l ON l.id = lp.language_id 
                WHERE lower(l.name) = ? OR lower(l.name) = ?
            """, (name.lower(), alt_name.lower()))

            row = cursor.fetchone()
            if not row:
                return None

            profile_id = row['id']
            profile_data = self._row_to_dict(row)

            # Fetch sections
            s_cursor = conn.execute("SELECT section_name, content FROM profile_sections WHERE profile_id = ?", (profile_id,))
            for s_row in s_cursor.fetchall():
                profile_data[s_row['section_name']] = s_row['content']

            return profile_data
        finally:
            conn.close()

    def get_concept_profiles(self) -> Dict[str, Any]:
        """Returns all loaded concept profile data."""
        if not self.use_sqlite:
            return self.concept_profiles

        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT c.name, cp.* 
                FROM concepts c 
                JOIN concept_profiles cp ON c.id = cp.concept_id
            """)
            profiles = {}
            for row in cursor.fetchall():
                concept_name = row['name']
                profile_id = row['id']
                profile_data = self._row_to_dict(row)

                # Fetch sections
                s_cursor = conn.execute("SELECT section_name, content FROM concept_profile_sections WHERE profile_id = ?", (profile_id,))
                for s_row in s_cursor.fetchall():
                    profile_data[s_row['section_name']] = s_row['content']

                profiles[concept_name] = profile_data
            return profiles
        finally:
            conn.close()

    def get_concept_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Returns the profile data for a given concept name.
        """
        if not self.use_sqlite:
            # 1. Try direct match
            if name in self.concept_profiles:
                return self.concept_profiles[name]

            # 2. Try alternative match (underscore -> space)
            alt_name = name.replace('_', ' ')
            if alt_name in self.concept_profiles:
                return self.concept_profiles[alt_name]
            return None

        conn = self._get_connection()
        try:
            # Try both direct and alternative names in SQL
            alt_name = name.replace('_', ' ')
            cursor = conn.execute("""
                SELECT cp.*, c.name, c.year as origin_year
                FROM concept_profiles cp 
                JOIN concepts c ON c.id = cp.concept_id 
                WHERE lower(c.name) = ? OR lower(c.name) = ?
            """, (name.lower(), alt_name.lower()))

            row = cursor.fetchone()
            if not row:
                return None

            profile_id = row['id']
            concept_id = row['concept_id']
            profile_data = self._row_to_dict(row)

            # Fetch sections
            s_cursor = conn.execute("SELECT section_name, content FROM concept_profile_sections WHERE profile_id = ?", (profile_id,))
            for s_row in s_cursor.fetchall():
                profile_data[s_row['section_name']] = s_row['content']

            # Fetch responsible people
            p_cursor = conn.execute("""
                SELECT p.name 
                FROM people p 
                JOIN concept_people cp ON p.id = cp.person_id 
                WHERE cp.concept_id = ?
            """, (concept_id,))
            profile_data['responsible_entity'] = ", ".join([r['name'] for r in p_cursor.fetchall()])

            return profile_data
        finally:
            conn.close()

    def get_combined_language_data(self, name: str) -> Optional[Dict[str, Any]]:
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

    def get_influences(self, name: str) -> Optional[Dict[str, Any]]:
        lang = self.get_language(name)
        if not lang:
            return None
        return {
            'influenced_by': lang.get('influenced_by', []),
            'influenced': lang.get('influenced', [])
        }

    def get_all_eras(self) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            return self.eras

        if not hasattr(self, '_eras_cache') or self._eras_cache is None:
            self._eras_cache = self._load_json('eras.json')
        return cast(List[Dict[str, Any]], self._eras_cache)

    def get_learning_paths(self) -> List[Dict[str, Any]]:
        """Returns all available learning paths (Odysseys)."""
        if not self.use_sqlite:
            return self.learning_paths

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM learning_paths")
            paths = [self._row_to_dict(row) for row in cursor.fetchall()]

            for path in paths:
                s_cursor = conn.execute("SELECT * FROM learning_path_steps WHERE path_id = ? ORDER BY step_order", (path['id'],))
                path['steps'] = [
                    {
                        "language": row['language_name'],
                        "milestone": row['milestone'],
                        "rationale": row['rationale'],
                        "challenge": row['challenge']
                    } for row in s_cursor.fetchall()
                ]
            return paths
        finally:
            conn.close()

    def get_learning_path(self, path_id: str) -> Optional[Dict[str, Any]]:
        """Returns a specific learning path by ID."""
        if not self.use_sqlite:
            for path in self.learning_paths:
                if path['id'] == path_id:
                    return path
            return None

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM learning_paths WHERE id = ?", (path_id,))
            row = cursor.fetchone()
            if not row:
                return None

            path = self._row_to_dict(row)
            s_cursor = conn.execute("SELECT * FROM learning_path_steps WHERE path_id = ? ORDER BY step_order", (path_id,))
            path['steps'] = [
                {
                    "language": row['language_name'],
                    "milestone": row['milestone'],
                    "rationale": row['rationale'],
                    "challenge": row['challenge']
                } for row in s_cursor.fetchall()
            ]
            return path
        finally:
            conn.close()

    def get_auto_odyssey(self, language_name: str) -> Optional[Dict[str, Any]]:
        """
        Generates a dynamic Odyssey based on the most influential descendants of a language.
        Uses a Recursive CTE to explore the lineage tree.
        """
        if not self.use_sqlite:
            # Fallback for non-SQLite: just direct descendants
            lang = self.get_language(language_name)
            if not lang: return None
            desc_names = lang.get('influenced', [])
            steps = []
            for name in desc_names[:4]:
                steps.append({
                    "language": name,
                    "milestone": "Influenced Descendant"
                })
            return {
                "id": f"auto_{language_name.lower()}",
                "title": f"The Legacy of {language_name}",
                "description": f"A dynamically generated journey through the most impactful languages influenced by {language_name}.",
                "steps": steps
            }

        conn = self._get_connection()
        try:
            query = """
            WITH RECURSIVE descendants AS (
                SELECT target_id, 1 as depth
                FROM influences
                WHERE source_id = (SELECT id FROM languages WHERE lower(name) = ? OR lower(display_name) = ?)

                UNION ALL

                SELECT i.target_id, d.depth + 1
                FROM influences i
                JOIN descendants d ON i.source_id = d.target_id
                WHERE d.depth < 3
            )
            SELECT DISTINCT l.name, l.display_name, l.influence_score
            FROM descendants d
            JOIN languages l ON d.target_id = l.id
            WHERE lower(l.name) != ?
            ORDER BY l.influence_score DESC
            LIMIT 4
            """

            cursor = conn.execute(query, (language_name.lower(), language_name.lower(), language_name.lower()))
            results = cursor.fetchall()

            if not results:
                return None

            steps = []
            for i, row in enumerate(results):
                steps.append({
                    "language": row['name'],
                    "milestone": f"Generation {i+1} Impact"
                })

            return {
                "id": f"auto_{language_name.lower()}",
                "title": f"The Legacy of {language_name}",
                "description": f"A dynamically generated journey through the most impactful descendants in the {language_name} lineage.",
                "steps": steps
            }
        finally:
            conn.close()

    def get_concepts_reference(self) -> Dict[str, Any]:
        """Returns the concepts reference metadata."""
        # Check common locations
        paths = [
            os.path.join(self.data_dir, 'docs', 'atlas_meta', 'concepts_reference.json'),
            os.path.join(self.data_dir, 'docs', 'concepts', 'concepts_reference.json')
        ]
        for p in paths:
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    return cast(Dict[str, Any], json.load(f))
        return {"concepts": []}

    def get_paradigm_matrix(self) -> Dict[str, Any]:
        """Returns the paradigm matrix dimensions."""
        p = os.path.join(self.data_dir, 'docs', 'paradigms', 'paradigm_matrix.json')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                return cast(Dict[str, Any], json.load(f))
        return {"dimensions": []}

    def get_all_people(self) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            return self.people

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT name FROM people ORDER BY name")
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_all_influences(self) -> List[Dict[str, Any]]:
        if not self.use_sqlite:
            return self.influences

        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT l1.name as 'from', l2.name as 'to'
                FROM influences i
                JOIN languages l1 ON i.source_id = l1.id
                JOIN languages l2 ON i.target_id = l2.id
            """)
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_all_clusters(self) -> List[str]:
        if not self.use_sqlite:
            clusters = set()
            for lang in self.languages:
                if 'cluster' in lang:
                    clusters.add(lang['cluster'])
            return sorted(list(clusters))

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT DISTINCT cluster FROM languages WHERE cluster IS NOT NULL ORDER BY cluster")
            return [row['cluster'] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_all_paradigms(self) -> List[str]:
        if not self.use_sqlite:
            paradigms: Set[str] = set()
            for lang in self.languages:
                if 'paradigms' in lang:
                    for p in lang['paradigms']:
                        paradigms.add(p)
            return sorted(list(paradigms))

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT name FROM paradigms ORDER BY name")
            return [row['name'] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_paradigm_info(self, name: str) -> Dict[str, Any]:
        if not self.use_sqlite:
            for p in self.paradigms:
                if p['name'].lower() == name.lower():
                    return p
            return {"name": name, "description": "A core model or style of computer programming."}

        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM paradigms WHERE lower(name) = ?", (name.lower(),))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return {"name": name, "description": "A core model or style of computer programming."}
        finally:
            conn.close()

    def search(self, query_term: str) -> List[Dict[str, Any]]:
        """Performs an advanced full-text search using FTS5 BM25 ranking and context snippets."""
        if not self.use_sqlite:
            # Simple in-memory search fallback
            results = []
            term = query_term.lower()
            for lang in self.get_all_languages():
                if term in lang['name'].lower() or term in lang.get('philosophy', '').lower():
                    results.append({
                        'category': 'language',
                        'title': lang['name'],
                        'snippet': lang.get('philosophy', '')[:200],
                        'language_id': lang.get('id')
                    })
            return results

        conn = self._get_connection()
        try:
            sql = """
                SELECT 
                    'language' as category, 
                    name as title, 
                    name as link_name,
                    snippet(fts_languages, -1, '<b>', '</b>', '...', 20) as snippet, 
                    bm25(fts_languages) as score,
                    language_id
                FROM fts_languages 
                WHERE fts_languages MATCH ?
                UNION ALL
                SELECT 
                    'profile' as category, 
                    language_name || ' (' || section_name || ')' as title, 
                    language_name as link_name,
                    snippet(fts_profiles, -1, '<b>', '</b>', '...', 20) as snippet, 
                    bm25(fts_profiles) as score,
                    language_id
                FROM fts_profiles
                WHERE fts_profiles MATCH ?
                UNION ALL
                SELECT 
                    'concept' as category, 
                    concept_name as title, 
                    concept_name as link_name,
                    snippet(fts_concept_profiles, -1, '<b>', '</b>', '...', 20) as snippet, 
                    bm25(fts_concept_profiles) as score,
                    concept_id as language_id
                FROM fts_concept_profiles
                WHERE fts_concept_profiles MATCH ?
                ORDER BY score
                LIMIT 30
            """
            cursor = conn.execute(sql, (query_term, query_term, query_term))
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Fallback for invalid FTS5 syntax
            return []
        finally:
            conn.close()

    def get_cluster_info(self, name: str) -> Dict[str, Any]:
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

