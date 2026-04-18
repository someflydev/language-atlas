# Content Completeness Planning Playbook

## Purpose

Use this playbook when the task is to write a new prompt series for the next
highest-value content completeness work, following the structure of
`.prompts/PROMPT_55.txt` through `.prompts/PROMPT_65.txt`.

## Load First

1. `AGENT.md`
2. `CLAUDE.md`
3. `.context/data-pipeline.md`
4. `.context/architecture.md`
5. `.context/commands.md`
6. `generated-reports/dark_matter_todo.json`
7. `.prompts/PROMPT_55.txt` through `.prompts/PROMPT_65.txt`
8. `git show --stat 660653b`

## Workflow

1. Determine the next available prompt number.
2. Read the current completeness backlog.
3. Rank the next highest-value content area.
4. Split the work into balanced prompt-sized batches.
5. Write one prompt file per batch with exact filenames, schemas, and
   verification commands.

## Planning Rules

- follow the existing prompt style closely
- keep each prompt finishable in one session
- avoid overlap across batches
- prefer structured, high-signal content gaps over vague cleanup
- include exact commit blocks

## Likely Inputs

- `missing_language_profiles`
- `missing_org_profiles`
- `missing_historical_events`
- direct profile-vs-source comparisons for people and concepts

## Output Standard

The resulting prompts should feel like a direct continuation of the existing
series, not a new workflow.
