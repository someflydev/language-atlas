# Database Schema

**File:** `language_atlas.sqlite` (gitignored — rebuild with `make build`)
**Builder:** `src/app/core/build_sqlite.py`

## Core Tables
| Table | Key Columns |
|---|---|
| `languages` | id, name, display_name, year, cluster, generation, philosophy, mental_model, complexity_bias, safety_model, typing_discipline, memory_management, is_keystone, influence_score |
| `paradigms` | id, name, description, year_introduced, motivation, languages (JSON), connected_paradigms (JSON), key_features (JSON) |
| `people` | id, name |
| `influences` | source_id → target_id (FK to languages) |
| `language_paradigms` | language_id, paradigm_id, order_index |
| `language_people` | language_id, person_id, role |

## Profile Tables (narrative content)
| Table | Notes |
|---|---|
| `language_profiles` | title, overview per language |
| `profile_sections` | section_name + content keyed to language_profile |
| `people_profiles` | title, overview per person |
| `people_profile_sections` | sections keyed to people_profile |
| `concept_profiles` | title, overview per concept |
| `concept_profile_sections` | sections keyed to concept_profile |
| `organization_profiles` | title, overview per org |
| `organization_profile_sections` | sections keyed to org_profile |

## Supporting Tables
| Table | Notes |
|---|---|
| `concepts` | id, name, description, year |
| `concept_people` | concept_id ↔ person_id |
| `concept_bullets` | bullet points for concept profiles |
| `organizations` | id, name, founded |
| `historical_events` | id, slug, title, date, overview |
| `event_sections` | sections keyed to historical_event |
| `era_summaries` | slug, title, overview, legacy_impact, diagram |
| `era_key_drivers` | era_id, name, description |
| `era_pivotal_languages` | era_id, name, description |
| `crossroads` | id, title, explanation |
| `modern_reactions` | id, theme, explanation |
| `timeline_periods` | id, era_or_period |
| `timeline_events` | period_id, year, description |
| `timeline_event_related` | event_id, related_name |
| `learning_paths` | id (text), title, description, type |
| `learning_path_steps` | path_id, language_name, milestone, rationale, challenge, step_order |

## FTS5 Virtual Table
```sql
CREATE VIRTUAL TABLE search_index USING fts5(
    entity_type UNINDEXED, entity_id UNINDEXED,
    title, content,
    tokenize='porter'
);
```

## Analytical Views (created by build_sqlite.py)
- `v_language_era_rankings` — RANK() by influence_score within era/cluster
- `v_paradigm_momentum` — cumulative language count per paradigm over time (window func)
- Additional lead/lag view for complexity/safety comparisons within cluster

## Recursive CTEs (runtime queries in DataLoader/InsightGenerator)
- `get_ancestors(language_id, max_depth)` — recursive influence chain going up
- `get_descendants(language_id, max_depth)` — recursive influence chain going down
- `get_auto_odyssey(name)` — dynamic learning path via influential descendants
- `InsightGenerator.calculate_influence_depth()` — transitive influence with depth
- `InsightGenerator.calculate_paradigm_volatility()` — paradigm intro by decade
