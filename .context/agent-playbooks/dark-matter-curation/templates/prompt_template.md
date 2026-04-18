# PROMPT_XX: Dark Matter Alias Expansion

## Objective

Expand the reviewed dark matter alias and canonical layer using only
high-confidence semantic merges already supported by Atlas source data.

## Mandatory First Steps

1. Read `AGENT.md` and `CLAUDE.md`.
2. Load `.context/data-pipeline.md`, `.context/architecture.md`, and
   `.context/commands.md`.
3. Read `.prompts/PROMPT_66.txt` and `.prompts/PROMPT_67.txt`.
4. Read `scripts/dark_matter_audit.py` and
   `tests/test_dark_matter_audit.py`.
5. Run `make dark-matter`.
6. Read `generated-reports/dark_matter_todo.json`.
7. Read `data/.dark_matter_aliases.json` and
   `data/.dark_matter_canonicals.json`.
8. Create `tmp/PROMPT_XX_checklist.md`.

## Task

- review conservative alias candidates
- add safe aliases and matching canonical entries
- extend focused tests
- re-run the audit

## Verification

- `make dark-matter`
- `uv run pytest tests/test_dark_matter_audit.py`
- `make audit`
