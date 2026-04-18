# PROMPT_XX: [Batch Title]

## Objective

Create a focused batch of missing Atlas content in one clear theme chosen from
the current highest-value completeness gaps.

## Mandatory First Steps

1. Read `AGENT.md` and `CLAUDE.md`.
2. Load required context files.
3. Read `generated-reports/dark_matter_todo.json`.
4. Compare the relevant source-of-truth dataset against the matching
   `data/docs/` profile directory.
5. Create `tmp/PROMPT_XX_checklist.md`.
6. Check off each item immediately after completing it.

## Selection Rationale

State briefly why this batch is high-priority now:

- direct completeness gap being closed
- narrative or lineage leverage
- why this grouping is coherent enough for one prompt

## Items To Create

List exact files, exact entities, and exact schema expectations.

## Verification

- `make build`
- `make audit`
- `make dark-matter`

## Commit

Provide an explicit Tim Pope style commit block.
