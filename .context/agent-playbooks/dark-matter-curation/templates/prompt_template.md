# PROMPT_XX: Dark Matter Alias Expansion

## Objective

Expand the reviewed dark matter alias and canonical layer using only
high-confidence semantic merges already supported by Atlas source data.

## Mandatory First Steps

1. Read `AGENT.md` and `CLAUDE.md`.
2. Load `.context/data-pipeline.md`, `.context/architecture.md`, and
   `.context/commands.md`.
3. Read
   `.context/agent-playbooks/dark-matter-curation/references/alias-policy.md`.
4. Optionally read `.prompts/PROMPT_66.txt` and `.prompts/PROMPT_67.txt`
   for historical examples only.
5. Read `scripts/dark_matter_audit.py` and
   `tests/test_dark_matter_audit.py`.
6. Run `make dark-matter`.
7. Read `generated-reports/dark_matter_todo.json`.
8. Read `data/.dark_matter_aliases.json` and
   `data/.dark_matter_canonicals.json`.
9. Create `tmp/PROMPT_XX_checklist.md`.

## Task

- review one narrow family of conservative alias candidates
- add safe aliases and matching canonical entries
- extend focused tests
- re-run the audit and inspect the delta
- repeat the pass until the next candidates become ambiguous or low-value

## Verification

- `make dark-matter`
- `uv run pytest tests/test_dark_matter_audit.py`
- `make audit`
