# Data Pipeline & Sources

## JSON Source Files (`data/`)
| File | Contents |
|---|---|
| `languages.json` | Core language records (name, year, cluster, generation, paradigms[], creators[], etc.) |
| `paradigms.json` | Paradigm records (name, description, year_introduced, motivation, languages, key_features) |
| `people.json` | Person records (name, + profile fields) |
| `concepts.json` | Concept records (name, description, year, responsible[]) |
| `influences.json` | Influence edges: [{source, target}] |
| `eras.json` | Era records (slug, title, etc.) |
| `learning_paths.json` | Odyssey definitions (id, title, steps[]) — loaded by DataLoader even in SQLite mode |

## Narrative Profile Directories (`data/docs/`)
| Directory | Profile fields required |
|---|---|
| `language_profiles/` | title, overview, historical_context, mental_model, key_innovations, tradeoffs, legacy, ai_assisted_discovery_missions |
| `concept_profiles/` | title, overview, historical_context, key_aspects, technical_implications, legacy, ai_assisted_discovery_missions |
| `people_profiles/` | title, overview, historical_context, pivotal_works, affiliations, legacy, ai_assisted_discovery_missions (+ optional mental_model) |
| `org_profiles/` | title, founded, overview, key_contributions, pivotal_people, legacy, ai_assisted_discovery_missions |
| `historical_events/` | title, date, overview, impact_on_computing, key_figures, legacy, ai_assisted_discovery_missions |
| `concept_combos/` | Multi-concept narrative docs |
| `concepts/` | Additional concept doc files |
| `atlas_meta/` | Internal architecture profiles (Pedagogical Engine, Zenith State) |

## Profile Filename Mapping
- Profile filenames are derived from canonical entity names by replacing spaces with underscores.
- Preserve punctuation that is part of the source-of-truth name instead of stripping it.
- Transliterate non-ASCII letters to the closest reasonable ASCII form in the filename.
- This is especially important for people profiles because filename stems are matched back to `data/people.json` names after underscore-to-space conversion and ASCII transliteration.
- Example: `Guy L. Steele` -> `Guy_L._Steele.json`; `Ole-Johan Dahl` -> `Ole-Johan_Dahl.json`; `José Valim` -> `Jose_Valim.json`.

## Build Pipeline
```bash
make build   # runs: uv run python -m app.core.build_sqlite
```
- Sets `USE_SQLITE=0` internally to force JSON reading
- Drops and recreates `language_atlas.sqlite` at repo root
- Populates all tables from JSON files
- Calculates `influence_score` (count of downstream dependents)
- Builds FTS5 `search_index` virtual table (porter tokenizer)
- Creates analytical views: `v_language_era_rankings`, `v_paradigm_momentum`

## DataLoader Modes
- **SQLite mode** (`USE_SQLITE=1`, default in app): reads from `language_atlas.sqlite`
  - `_get_connection()` returns read-only connection (`file:...?mode=ro`)
- **JSON mode** (`USE_SQLITE=0`): loads all JSON into memory (used by build script)
  - Supports both single-file (`languages.json`) and directory-based loading
  - `_load_json()` merges data from all `.json` files in a `<dataset>/` directory

## Quality Gates
```bash
make audit        # AtlasAuditor — schema validation + referential integrity
make dark-matter  # scripts/dark_matter_audit.py — missing profiles
make test         # pytest (fast unit + consistency)
make harden       # type-check + audit + test
```
- `generated-reports/dark_matter_todo.json` — authoritative list of missing profiles
