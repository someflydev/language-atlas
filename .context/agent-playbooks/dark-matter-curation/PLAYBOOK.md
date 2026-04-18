# Dark Matter Curation Playbook

## Purpose

Use this playbook when the task is to improve semantic consolidation for the
dark matter audit by editing:

- `data/.dark_matter_aliases.json`
- `data/.dark_matter_canonicals.json`

This playbook is intentionally agent-neutral. It should work whether the
operator is Codex, Claude, Gemini, or another assistant.

## Load First

1. `AGENT.md`
2. `CLAUDE.md`
3. `.context/data-pipeline.md`
4. `.context/architecture.md`
5. `.context/commands.md`
6. `.context/agent-playbooks/dark-matter-curation/references/alias-policy.md`
7. `scripts/dark_matter_audit.py`
8. `tests/test_dark_matter_audit.py`
9. `generated-reports/dark_matter_todo.json`
10. `data/.dark_matter_aliases.json`
11. `data/.dark_matter_canonicals.json`

## Optional Historical Context

Load these only if you need prior dark-matter curation examples or prompt
wording patterns:

- `.prompts/PROMPT_66.txt`
- `.prompts/PROMPT_67.txt`

## Workflow

1. Run `make dark-matter` if the report may be stale.
2. Read the report and identify a small, safe batch of duplicate-looking
   entries for the current pass.
3. Use `scripts/dark_matter_alias_candidates.py` to generate a conservative
   candidate set.
4. Verify each candidate against structured source data, existing profile
   files, and the alias policy reference before accepting it.
5. Add reviewed entries to the hidden alias and canonical files.
6. Extend focused tests in `tests/test_dark_matter_audit.py`.
7. Re-run the audit and inspect the report delta.
8. Repeat the pass with another small batch until the remaining candidates are
   ambiguous, low-value, or no longer safely reviewable in the current session.

## Looping Guidance

Treat dark matter curation as an iterative consolidation loop, not as a
one-shot cleanup.

For each pass:

1. Pick one narrow family of duplicates, such as year-suffixed language names,
   descriptor-suffixed people, or obvious organization variants.
2. Add only high-confidence alias and canonical entries for that family.
3. Add or extend tests that cover the new normalization behavior.
4. Re-run `make dark-matter` and confirm the specific entries disappear.
5. Stop the pass when the remaining candidates require speculative semantic
   merges instead of mechanical normalization.

Good stopping condition:

- the next unresolved candidates are ambiguous
- the next batch would require broader source-data fixes instead of aliasing
- the report delta from additional safe merges is flattening out

## Review Rules

- Prefer exact known entities with extra years or descriptor suffixes.
- Prefer exact people, languages, organizations, and historical events.
- Skip ambiguous cases.
- Do not merge distinct concepts just because they are historically related.
- Do not use alias files as a substitute for better source coverage.

## Deliverables

- updated hidden alias and canonical files
- focused resolver tests
- regenerated `generated-reports/dark_matter_todo.json`

## Verification

- `make dark-matter`
- `uv run pytest tests/test_dark_matter_audit.py`
- `make audit`
- `make test` if the session budget allows it
