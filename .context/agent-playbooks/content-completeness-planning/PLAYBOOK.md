# Content Completeness Planning Playbook

## Purpose

Use this playbook when the task is to write a new prompt series for the next
highest-value content completeness work using current Atlas data, current
dark-matter output, and the established prompt style.

## Load First

1. `AGENT.md`
2. `CLAUDE.md`
3. `.context/data-pipeline.md`
4. `.context/architecture.md`
5. `.context/commands.md`
6. `generated-reports/dark_matter_todo.json`
7. `data/people.json`
8. `data/languages.json`
9. `data/concepts.json`
10. `data/docs/people_profiles/`
11. `data/docs/language_profiles/`
12. `data/docs/concept_profiles/`
13. `data/docs/org_profiles/`
14. `data/docs/historical_events/`

## Optional Style Context

Load a few recent prompt files only to match wording and structure, not to
decide what should be prioritized next.

Suggested examples:

- `.prompts/PROMPT_68.txt`
- `.prompts/PROMPT_69.txt`
- one or two representative earlier completeness prompts if needed

## Workflow

1. Determine the next available prompt number.
2. Read the current completeness backlog from `generated-reports/dark_matter_todo.json`.
3. Build the direct completeness picture from source-of-truth datasets versus
   existing profile directories.
4. Rank the next highest-value content area using the prioritization rules
   below.
5. Split the work into balanced prompt-sized batches.
6. Write one prompt file per batch with exact filenames, schemas, and
   verification commands.

## Planning Rules

- follow the existing prompt style closely
- keep each prompt finishable in one session
- avoid overlap across batches
- prefer structured, high-signal content gaps over vague cleanup
- include exact commit blocks
- do not let older prompt series determine future priorities by inertia

## Prioritization Rules

Prioritization must be data-driven and re-evaluated each time. Do not hardcode
specific names or topics in the playbook itself.

Rank candidate batches higher when they score well on several of these axes:

1. Direct completeness gap
   - entities present in `data/*.json` but still missing matching profiles
   - especially people, languages, organizations, and historical events with
     exact source-of-truth entries
2. Atlas centrality
   - creators or concepts tied to major languages, paradigms, or narrative
     hubs already covered elsewhere in the Atlas
   - figures repeatedly surfaced in `generated-reports/dark_matter_todo.json`
     or referenced across existing profiles
3. Narrative leverage
   - batches that close obvious historical holes and improve cross-link density
   - missing profiles that unlock clearer lineage stories across multiple
     existing pages
4. Batch coherence
   - items that can be grouped into one historically coherent prompt without
     becoming a grab bag
5. Verification simplicity
   - work that can be clearly verified through build, audit, route checks, and
     dark-matter delta

Rank candidate batches lower when they are:

- mostly speculative dark matter with no clear source-of-truth anchor
- dependent on unresolved alias/canonical cleanup first
- too broad to finish in one prompt session
- redundant with very recent prompt batches

## Recommended Planning Method

When deciding the next prompt series:

1. Start with direct dataset coverage gaps, not only with the current prompt
   history.
2. Compare `data/people.json`, `data/languages.json`, and other source files
   against the corresponding `data/docs/` directories.
3. Cross-check that list against `generated-reports/dark_matter_todo.json` to
   see which missing profiles are also creating large amounts of downstream
   dark matter.
4. Prefer missing entities that are both source-of-truth omissions and major
   lineage anchors in the existing Atlas.
5. Only then shape the chosen work into prompt-sized coherent batches.

## Likely Inputs

- `missing_language_profiles`
- `missing_org_profiles`
- `missing_historical_events`
- direct profile-vs-source comparisons for people and concepts
- repeated high-signal names in `missing_entities`
- current coverage diffs between `data/*.json` and `data/docs/*_profiles/`

## Output Standard

The resulting prompts should feel like a direct continuation of the existing
series, but the prioritization behind them should come from current repo data,
not from stale prompt habits.
