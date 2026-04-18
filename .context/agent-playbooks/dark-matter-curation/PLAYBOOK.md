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
4. If the conservative candidate set is exhausted, identify one narrow family
   of judgment-heavy candidates directly from the report.
5. Verify each candidate against structured source data, existing profile
   files, and the alias policy reference before accepting it.
6. Add reviewed entries to the hidden alias and canonical files.
7. Extend focused tests in `tests/test_dark_matter_audit.py`.
8. Re-run the audit and inspect the report delta.
9. Repeat the pass with another small batch until the remaining candidates are
   ambiguous, low-value, or no longer safely reviewable in the current session.

## Looping Guidance

Treat dark matter curation as an iterative consolidation loop, not as a
one-shot cleanup.

For each pass:

1. Pick one narrow family of duplicates, such as year-suffixed language names,
   descriptor-suffixed people, organization labels, or project-vs-language
   references that clearly collapse to one known Atlas entity.
2. Prefer conservative candidates first. When those are exhausted, move to a
   judgment-heavy pass only if the family can still be reviewed consistently.
3. Add only reviewed alias and canonical entries for that family.
4. Add or extend tests that cover the new normalization behavior.
5. Re-run `make dark-matter` and confirm the specific entries disappear.
6. Stop the pass when the remaining candidates require speculative semantic
   merges instead of reviewed normalization.

## Judgment-Heavy Pass Rules

Judgment-heavy normalization is allowed when the goal is to consolidate noisy
dark matter that the conservative script will not propose, but it still needs
clear evidence.

Allowed examples:

- descriptor-heavy references that clearly point to one known person
- product, project, or platform phrases that clearly refer to one known Atlas
  language or organization
- historically specific labels that are not exact string variants but are
  obviously the same entity in repo context

Required evidence before accepting a merge:

1. the target entity already exists clearly in Atlas source data or docs
2. the candidate phrase is used in repo content as a label for that target,
   not merely as a related concept
3. collapsing the phrase does not erase a genuinely separate concept, event,
   or organization
4. a focused test can express the reviewed behavior

When making a judgment-heavy merge, record the reasoning in the commit message
or handoff summary so future passes can distinguish reviewed policy from
accidental cleanup.

Good stopping condition:

- the next unresolved candidates are ambiguous
- the next batch would require broader source-data fixes instead of aliasing
- the report delta from additional safe merges is flattening out

## Review Rules

- Prefer exact known entities with extra years or descriptor suffixes.
- Prefer exact people, languages, organizations, and historical events.
- Judgment-heavy normalization is allowed only for narrow, reviewable families.
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
