#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def validate():
    root = Path(__file__).parent.parent
    data_path = root / 'data' / 'languages.json'

    if not data_path.exists():
        print(f"Error: {data_path} not found")
        sys.exit(1)

    with open(data_path, 'r', encoding='utf-8') as f:
        try:
            languages = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse JSON: {e}")
            sys.exit(1)

    all_language_names = {lang.get('name') for lang in languages if 'name' in lang}
    errors = []

    required_keys = [
        'name', 'year', 'creators', 'paradigms', 'cluster', 'generation',
        'primary_use_cases', 'key_innovations', 'influenced_by', 'influenced',
        'philosophy', 'mental_model', 'complexity_bias', 'safety_model',
        'typing_discipline', 'memory_management', 'is_keystone'
    ]

    complexity_bias_enum = ['low', 'medium', 'high']
    # Canonical generations from CONCEPTS.md and eras.json
    generation_enum = ['dawn', 'early', 'web1', 'cloud', 'renaissance', 'autonomic']
    # Based on prompt: safety_model, typing_discipline, memory_management ENUM: manual, runtime, compile_time, hybrid
    generic_enum = ['manual', 'runtime', 'compile_time', 'hybrid']

    for i, lang in enumerate(languages):
        name = lang.get('name', f"Entry #{i}")

        # Check required keys
        for key in required_keys:
            if key not in lang:
                errors.append(f"Language '{name}' is missing required key: '{key}'")

        # Check types (basic checks to avoid crashes)
        if 'is_keystone' in lang and not isinstance(lang['is_keystone'], bool):
            errors.append(f"Language '{name}': 'is_keystone' must be a boolean, got {type(lang['is_keystone']).__name__}")

        if 'year' in lang and not isinstance(lang['year'], int):
            errors.append(f"Language '{name}': 'year' must be an integer, got {type(lang['year']).__name__}")

        # Check enums
        if 'complexity_bias' in lang and lang.get('complexity_bias') not in complexity_bias_enum:
            errors.append(f"Language '{name}': 'complexity_bias' must be one of {complexity_bias_enum}, got '{lang.get('complexity_bias')}'")

        if 'generation' in lang and lang.get('generation') not in generation_enum:
            errors.append(f"Language '{name}': 'generation' must be one of {generation_enum}, got '{lang.get('generation')}'")

        for key in ['safety_model', 'typing_discipline', 'memory_management']:
            if key in lang and lang.get(key) not in generic_enum:
                errors.append(f"Language '{name}': '{key}' must be one of {generic_enum}, got '{lang.get(key)}'")

        # Cross-reference influenced_by
        if 'influenced_by' in lang and isinstance(lang['influenced_by'], list):
            for ref in lang['influenced_by']:
                if ref not in all_language_names:
                    errors.append(f"Language '{name}' references unknown language in 'influenced_by': '{ref}'")

        # Cross-reference influenced
        if 'influenced' in lang and isinstance(lang['influenced'], list):
            for ref in lang['influenced']:
                if ref not in all_language_names:
                    errors.append(f"Language '{name}' references unknown language in 'influenced': '{ref}'")

    if errors:
        print(f"Validation failed with {len(errors)} errors:")
        for error in errors[:20]: # Show only first 20 errors to avoid flooding
            print(f"  - {error}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors.")
        sys.exit(1)

    print("Validation successful: All data conforms to schema and references are intact.")
    sys.exit(0)

if __name__ == "__main__":
    validate()
