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
6. `.prompts/PROMPT_66.txt`
7. `.prompts/PROMPT_67.txt`
8. `scripts/dark_matter_audit.py`
9. `tests/test_dark_matter_audit.py`
10. `generated-reports/dark_matter_todo.json`
11. `data/.dark_matter_aliases.json`
12. `data/.dark_matter_canonicals.json`

## Workflow

1. Run `make dark-matter` if the report may be stale.
2. Read the report and identify duplicate-looking entries.
3. Use `scripts/dark_matter_alias_candidates.py` to generate a conservative
   candidate set.
4. Verify each candidate against structured source data or existing profile
   files before accepting it.
5. Add reviewed entries to the hidden alias and canonical files.
6. Extend focused tests in `tests/test_dark_matter_audit.py`.
7. Re-run the audit and inspect the report delta.

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
