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

    def _load_json(self, filename):
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            return []
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

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

    def get_all_paradigms(self):
        return self.paradigms

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
