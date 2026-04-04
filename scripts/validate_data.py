#!/usr/bin/env python3
import json
import sys
import sqlite3
from pathlib import Path

def validate_json(data_path):
    print(f"[*] Validating JSON: {data_path.name}")
    if not data_path.exists():
        print(f"Error: {data_path} not found")
        return False
        
    with open(data_path, 'r', encoding='utf-8') as f:
        try:
            languages = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse JSON: {e}")
            return False

    all_language_names = {lang.get('name') for lang in languages if 'name' in lang}
    all_display_names = {lang.get('display_name') for lang in languages if 'display_name' in lang}
    errors = []
    warnings = []

    required_keys = [
        'name', 'year', 'creators', 'paradigms', 'cluster', 'generation',
        'primary_use_cases', 'key_innovations', 'influenced_by', 'influenced',
        'philosophy', 'mental_model', 'complexity_bias', 'safety_model',
        'typing_discipline', 'memory_management', 'is_keystone'
    ]

    complexity_bias_enum = ['low', 'medium', 'high']
    generation_enum = ['dawn', 'early', 'web1', 'cloud', 'renaissance', 'autonomic']
    safety_model_enum = ['manual', 'runtime', 'compile_time', 'hybrid']
    typing_discipline_enum = ['manual', 'runtime', 'compile_time', 'hybrid']
    memory_management_enum = ['manual', 'runtime', 'compile_time', 'hybrid']

    for i, lang in enumerate(languages):
        name = lang.get('name', f"Entry #{i}")

        for key in required_keys:
            if key not in lang:
                errors.append(f"Language '{name}' is missing required key: '{key}'")

        if 'is_keystone' in lang and not isinstance(lang['is_keystone'], bool):
            errors.append(f"Language '{name}': 'is_keystone' must be a boolean")

        if 'year' in lang and not isinstance(lang['year'], int):
            errors.append(f"Language '{name}': 'year' must be an integer")

        if 'complexity_bias' in lang and lang.get('complexity_bias') not in complexity_bias_enum:
            errors.append(f"Language '{name}': 'complexity_bias' must be one of {complexity_bias_enum}")

        if 'generation' in lang and lang.get('generation') not in generation_enum:
            errors.append(f"Language '{name}': 'generation' must be one of {generation_enum}")

        if 'safety_model' in lang and lang.get('safety_model') not in safety_model_enum:
             errors.append(f"Language '{name}': 'safety_model' must be one of {safety_model_enum}")

        if 'typing_discipline' in lang and lang.get('typing_discipline') not in typing_discipline_enum:
             errors.append(f"Language '{name}': 'typing_discipline' must be one of {typing_discipline_enum}")

        if 'memory_management' in lang and lang.get('memory_management') not in memory_management_enum:
             errors.append(f"Language '{name}': 'memory_management' must be one of {memory_management_enum}")

        if 'influenced_by' in lang and isinstance(lang['influenced_by'], list):
            for ref in lang['influenced_by']:
                if ref not in all_language_names and ref not in all_display_names:
                    warnings.append(f"Language '{name}' references unknown language in 'influenced_by': '{ref}'")

        if 'influenced' in lang and isinstance(lang['influenced'], list):
            for ref in lang['influenced']:
                if ref not in all_language_names and ref not in all_display_names:
                    warnings.append(f"Language '{name}' references unknown language in 'influenced': '{ref}'")

    if warnings:
        print(f"JSON validation found {len(warnings)} potential issues (warnings):")
        for warning in warnings[:10]:
            print(f"  - {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more warnings.")

    if errors:
        print(f"JSON Validation failed with {len(errors)} errors:")
        for error in errors[:20]:
            print(f"  - {error}")
        return False

    print("OK: JSON validation successful.")
    return True

def validate_sqlite(db_path):
    print(f"[*] Validating SQLite: {db_path.name}")
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    if db_path.stat().st_size == 0:
        print(f"Error: Database file at {db_path} is empty")
        return False

    errors = []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Referential Integrity: influences
        cursor.execute("SELECT COUNT(*) FROM influences WHERE source_id NOT IN (SELECT id FROM languages)")
        orphans = cursor.fetchone()[0]
        if orphans > 0:
            errors.append(f"Found {orphans} orphaned source_id in 'influences' table")

        cursor.execute("SELECT COUNT(*) FROM influences WHERE target_id NOT IN (SELECT id FROM languages)")
        orphans = cursor.fetchone()[0]
        if orphans > 0:
            errors.append(f"Found {orphans} orphaned target_id in 'influences' table")

        # 2. Referential Integrity: language_paradigms
        cursor.execute("SELECT COUNT(*) FROM language_paradigms WHERE language_id NOT IN (SELECT id FROM languages)")
        orphans = cursor.fetchone()[0]
        if orphans > 0:
            errors.append(f"Found {orphans} orphaned language_id in 'language_paradigms' table")
        
        cursor.execute("SELECT COUNT(*) FROM language_paradigms WHERE paradigm_id NOT IN (SELECT id FROM paradigms)")
        orphans = cursor.fetchone()[0]
        if orphans > 0:
            errors.append(f"Found {orphans} orphaned paradigm_id in 'language_paradigms' table")

        # 3. FTS Index Integrity
        cursor.execute("SELECT (SELECT COUNT(*) FROM languages) - (SELECT COUNT(*) FROM fts_languages)")
        diff = abs(cursor.fetchone()[0])
        if diff > 0:
            errors.append(f"FTS index 'fts_languages' is out of sync by {diff} rows")

        # fts_profiles includes both profile_sections and overviews from language_profiles
        cursor.execute("SELECT (SELECT COUNT(*) FROM profile_sections) + (SELECT COUNT(*) FROM language_profiles WHERE overview IS NOT NULL AND overview != '') - (SELECT COUNT(*) FROM fts_profiles)")
        diff = abs(cursor.fetchone()[0])
        if diff > 0:
            errors.append(f"FTS index 'fts_profiles' is out of sync by {diff} rows (expected section_count + overview_count)")

        # 4. Era keys check
        cursor.execute("SELECT COUNT(*) FROM languages WHERE generation IS NULL OR generation = ''")
        missing_gen = cursor.fetchone()[0]
        if missing_gen > 0:
            errors.append(f"Found {missing_gen} languages with missing generation field")

        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
        return False

    if errors:
        print(f"SQLite Validation failed with {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("OK: SQLite validation successful.")
    return True

def main():
    root = Path(__file__).parent.parent
    data_path = root / 'data' / 'languages.json'
    db_path = root / 'language_atlas.sqlite'

    json_ok = validate_json(data_path)
    sqlite_ok = validate_sqlite(db_path)

    if not json_ok or not sqlite_ok:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
