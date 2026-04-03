import json
import os

class DataLoader:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Assume we are in src/app/core/data_loader.py
            # Root is 3 levels up
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            self.data_dir = os.path.join(base_dir, 'data')
        else:
            self.data_dir = data_dir
        self.languages = self._load_json('languages.json')
        self.paradigms = self._load_json('paradigms.json')
        self.eras = self._load_json('eras.json')
        self.concepts = self._load_json('concepts.json')
        self.influences = self._load_json('influences.json')
        self.people = self._load_json('people.json')
        self.language_profiles = self._load_language_profiles()

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

    def get_all_languages(self, filter_gen=None, filter_cluster=None):
        langs = self.languages
        if filter_gen:
            langs = [l for l in langs if l.get('generation', '').lower() == filter_gen.lower()]
        if filter_cluster:
            langs = [l for l in langs if l.get('cluster', '').lower() == filter_cluster.lower()]
        return langs

    def get_language(self, name):
        for lang in self.languages:
            if lang['name'].lower() == name.lower():
                return lang
        return None

    def get_language_profiles(self):
        """Returns all loaded language profile data."""
        return self.language_profiles

    def get_language_profile(self, name):
        """
        Returns the profile data for a given language name.
        Handles name normalization to match filenames.
        """
        # 1. Try direct match
        if name in self.language_profiles:
            return self.language_profiles[name]
        
        # 2. Try normalized match (space -> underscore)
        normalized_name = name.replace(' ', '_')
        if normalized_name in self.language_profiles:
            return self.language_profiles[normalized_name]
            
        return None

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
        return self.eras

    def get_all_people(self):
        return self.people

    def get_all_influences(self):
        return self.influences

    def get_all_clusters(self):
        clusters = set()
        for lang in self.languages:
            if 'cluster' in lang:
                clusters.add(lang['cluster'])
        return sorted(list(clusters))

    def get_all_paradigms(self):
        paradigms = set()
        for lang in self.languages:
            if 'paradigms' in lang:
                for p in lang['paradigms']:
                    paradigms.add(p)
        return sorted(list(paradigms))

    def get_paradigm_info(self, name):
        for p in self.paradigms:
            if p['name'].lower() == name.lower():
                return p
        return {"name": name, "description": "A core model or style of computer programming."}

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
