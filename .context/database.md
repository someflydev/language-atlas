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

## Closure Tables (Materialized at Build Time)
| Table | Notes |
|---|---|
| `language_ancestry` | root_language_id, ancestor_language_id, min traversal depth, bounded path_count |
| `language_descendants` | root_language_id, descendant_language_id, min traversal depth, bounded path_count |
| `language_reachability` | from_language_id, to_language_id, min_depth, path_count copied from descendants |
| `language_lineage_paths_bounded` | representative bounded paths as language-name path_text plus edge_types_text |

`DataLoader.get_ancestors()` and `DataLoader.get_descendants()` use these
materialized tables for runtime queries. The recursive
`v_language_ancestors` and `v_language_descendants` views remain in the schema
as reference implementations.

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
- `get_ancestors(language_id, max_depth)` uses `language_ancestry`; the older recursive view remains available for reference checks
- `get_descendants(language_id, max_depth)` uses `language_descendants`; the older recursive view remains available for reference checks
- `get_auto_odyssey(name)` — dynamic learning path via influential descendants
- `InsightGenerator.calculate_influence_depth()` — transitive influence with depth
- `InsightGenerator.calculate_paradigm_volatility()` — paradigm intro by decade

## Semantic Field Definitions

These fields appear on language records in both `data/languages.json` and
the `languages` SQLite table. Valid values are enumerated below.

### `cluster`
Functional domain or ecosystem the language primarily targets.

| Value | Meaning |
|---|---|
| `AI` | Machine learning, neural networks, AI research |
| `academic` | Research or teaching languages |
| `backend` | Server-side application development |
| `business` | Enterprise, data processing, business logic |
| `cloud` | Cloud-native infrastructure, serverless |
| `data` | Data analysis, pipelines, transformation |
| `education` | Languages designed explicitly for learning |
| `enterprise` | Large-scale enterprise systems |
| `finance` | Financial modeling, quantitative computing |
| `frontend` | Browser / UI / client-side development |
| `historical` | Pre-modern or obsolete languages |
| `infra` | Infrastructure tooling, configuration, DevOps |
| `mathematics` | Formal computation, symbolic math, proofs |
| `safety-critical` | Avionics, medical devices, real-time systems |
| `scientific` | Scientific computing, simulation |
| `scripting` | Automation, glue code, shell-level tasks |
| `systems` | Operating systems, compilers, low-level code |
| `web` | Full-stack web development |

### `generation`
Broad era in which the language emerged and came to maturity.

| Value | Approximate period | Character |
|---|---|---|
| `dawn` | Pre-1960 | Assembly, batch processing, machine-oriented |
| `early` | 1960s-1970s | Structured, procedural, first HLLs |
| `web1` | 1980s-1990s | OOP wave, scripting, early internet languages |
| `cloud` | 2000s | Managed runtimes, web frameworks, dynamic languages |
| `renaissance` | 2010s | Type-safe systems, functional revival, polyglot era |
| `autonomic` | 2020s+ | AI-assisted, probabilistic, self-tuning runtimes |

### `is_keystone`
Boolean. A keystone language is one that is historically foundational:
either a precursor artifact (Turing Machine, Lambda Calculus) or a
language whose design decisions defined the conceptual vocabulary for
everything that followed (C, LISP, Smalltalk). Keystones are not
necessarily influential in the graph sense; they are conceptually
load-bearing.

### `influence_score`
Integer. Calculated at build time as the count of languages in
`influences.json` that list this language as a source (direct
downstream dependents only, not transitive). A score of 0 means no
language in the corpus explicitly cites this one as an influence.

### `complexity_bias`
The language's general posture toward feature surface area and
expressible abstraction.

| Value | Meaning |
|---|---|
| `low` | Minimal, sparse syntax and feature set (Go, Lua) |
| `medium` | Balanced; enough abstraction without excessive ceremony |
| `high` | Rich type systems, heavy abstraction, steep learning curve (C++, Scala) |

### `safety_model`
When and how the language enforces correctness and prevents
undefined behavior.

| Value | Meaning |
|---|---|
| `compile_time` | Safety guaranteed by the type system before execution (Rust, Haskell) |
| `runtime` | Safety enforced by bounds checks, GC, and exceptions at runtime (Java, Python) |
| `manual` | Programmer is responsible; no automatic guarantees (C, Assembly) |
| `hybrid` | Mix of compile-time checks and runtime guards (Ada, Swift) |

### `typing_discipline`
When type information is resolved and checked.

| Value | Meaning |
|---|---|
| `compile_time` | All types resolved and checked before execution (C, Go, Rust) |
| `runtime` | Types resolved and checked at execution (Python, Ruby, JavaScript) |
| `manual` | No type system; programmer manages representation directly (Assembly) |
| `hybrid` | Gradual typing or optional annotations (TypeScript, Typed Racket) |

### `memory_management`
How memory is allocated and freed.

| Value | Meaning |
|---|---|
| `manual` | Programmer allocates and frees explicitly (C, C++) |
| `runtime` | Garbage collector manages heap automatically (Java, Python, Go) |
| `compile_time` | Ownership/borrow system verifies lifetimes statically (Rust) |
