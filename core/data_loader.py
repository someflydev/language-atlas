import json
import os

class DataLoader:
    def __init__(self, data_dir='data'):
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
