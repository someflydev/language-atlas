import json
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

class AtlasAuditor:
    def __init__(self, data_path: Optional[Path] = None, db_path: Optional[Path] = None) -> None:
        root = Path(__file__).parent.parent.parent.parent
        self.data_path = data_path or root / 'data' / 'languages.json'
        self.db_path = db_path or root / 'language_atlas.sqlite'
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def clear(self) -> None:
        self.errors = []
        self.warnings = []

    def validate_json(self) -> bool:
        """Validates the raw languages.json file."""
        if not self.data_path.exists():
            self.errors.append(f"Data file not found: {self.data_path}")
            return False
            
        with open(self.data_path, 'r', encoding='utf-8') as f:
            try:
                languages: List[Dict[str, Any]] = json.load(f)
            except json.JSONDecodeError as e:
                self.errors.append(f"Failed to parse JSON: {e}")
                return False

        all_language_names: Set[str] = {lang.get('name', '') for lang in languages if 'name' in lang}
        all_display_names: Set[str] = {lang.get('display_name', '') for lang in languages if 'display_name' in lang}

        required_keys = [
            'name', 'year', 'creators', 'paradigms', 'cluster', 'generation',
            'primary_use_cases', 'key_innovations', 'influenced_by', 'influenced',
            'philosophy', 'mental_model', 'complexity_bias', 'safety_model',
            'typing_discipline', 'memory_management', 'is_keystone'
        ]

        enums: Dict[str, List[str]] = {
            'complexity_bias': ['low', 'medium', 'high'],
            'generation': ['dawn', 'early', 'web1', 'cloud', 'renaissance', 'autonomic'],
            'safety_model': ['manual', 'runtime', 'compile_time', 'hybrid'],
            'typing_discipline': ['manual', 'runtime', 'compile_time', 'hybrid'],
            'memory_management': ['manual', 'runtime', 'compile_time', 'hybrid']
        }

        for i, lang in enumerate(languages):
            name = lang.get('name', f"Entry #{i}")

            for key in required_keys:
                if key not in lang:
                    self.errors.append(f"Language '{name}' is missing required key: '{key}'")

            for field, allowed in enums.items():
                val = lang.get(field)
                if field in lang and val not in allowed:
                    self.errors.append(f"Language '{name}': '{field}' must be one of {allowed}, got '{val}'")

            if 'is_keystone' in lang and not isinstance(lang['is_keystone'], bool):
                self.errors.append(f"Language '{name}': 'is_keystone' must be a boolean")

            if 'year' in lang and not isinstance(lang['year'], int):
                self.errors.append(f"Language '{name}': 'year' must be an integer")

            # Semantic Orphans Check (JSON level)
            if not lang.get('influenced_by') and not lang.get('influenced'):
                 self.warnings.append(f"Semantic Orphan: Language '{name}' has no listed influences.")
            
            if not lang.get('paradigms'):
                 self.warnings.append(f"Semantic Orphan: Language '{name}' has no listed paradigms.")

            # Reference Checks
            for ref_field in ['influenced_by', 'influenced']:
                refs = lang.get(ref_field)
                if isinstance(refs, list):
                    for ref in refs:
                        if ref not in all_language_names and ref not in all_display_names:
                            self.warnings.append(f"Language '{name}' references unknown language in '{ref_field}': '{ref}'")

        return len(self.errors) == 0

    def validate_sqlite(self) -> bool:
        """Validates the SQLite database integrity and sync state."""
        if not self.db_path.exists():
            self.errors.append(f"Database not found at {self.db_path}")
            return False
        
        if self.db_path.stat().st_size == 0:
            self.errors.append(f"Database file is empty")
            return False

        conn: Optional[sqlite3.Connection] = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Referential Integrity
            checks = [
                ("influences", "source_id", "languages", "id"),
                ("influences", "target_id", "languages", "id"),
                ("language_paradigms", "language_id", "languages", "id"),
                ("language_paradigms", "paradigm_id", "paradigms", "id")
            ]
            for table, col, ref_table, ref_col in checks:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} NOT IN (SELECT {ref_col} FROM {ref_table})")
                row = cursor.fetchone()
                orphans = row[0] if row else 0
                if orphans > 0:
                    self.errors.append(f"Found {orphans} orphaned {col} in '{table}' table")

            # 2. FTS Index Integrity
            cursor.execute("SELECT (SELECT COUNT(*) FROM languages) - (SELECT COUNT(DISTINCT entity_id) FROM search_index WHERE entity_type = 'language')")
            row = cursor.fetchone()
            diff = abs(row[0]) if row else 0
            if diff > 0:
                self.errors.append(f"FTS index 'search_index' is out of sync by {diff} rows")

            # 3. Semantic Orphans Check (SQL level)
            cursor.execute("""
                SELECT name FROM languages 
                WHERE id NOT IN (SELECT source_id FROM influences)
                AND id NOT IN (SELECT target_id FROM influences)
            """)
            orphans = cursor.fetchall()
            for row in orphans:
                self.warnings.append(f"Semantic Orphan (SQL): Language '{row['name']}' has no relationships in 'influences' table.")

            cursor.execute("""
                SELECT name FROM languages 
                WHERE id NOT IN (SELECT language_id FROM language_paradigms)
            """)
            orphans = cursor.fetchall()
            for row in orphans:
                self.warnings.append(f"Semantic Orphan (SQL): Language '{row['name']}' has no associated paradigms.")

        except sqlite3.Error as e:
            self.errors.append(f"SQLite Error: {e}")
            return False
        finally:
            if conn:
                conn.close()

        return len(self.errors) == 0

    def run_all(self) -> Tuple[bool, List[str], List[str]]:
        self.clear()
        json_ok = self.validate_json()
        sqlite_ok = self.validate_sqlite()
        return (json_ok and sqlite_ok), self.errors, self.warnings

if __name__ == "__main__":
    auditor = AtlasAuditor()
    success, errs, warns = auditor.run_all()
    
    if warns:
        print(f"\n[!] Warnings ({len(warns)}):")
        for w in warns: print(f"  - {w}")
        
    if not success:
        print(f"\n[FAIL] Errors ({len(errs)}):")
        for e in errs: print(f"  - {e}")
        sys.exit(1)
    
    print("\n[PASS] Atlas Audit successful.")
