# Agent Preferences

## Protocol
- **Load First:** Always read `AGENT.md` before executing any instructions from `.prompts/PROMPT_XX.txt` or any other directive. This ensures all architectural and stylistic mandates are followed.
- **Ignore human-notes.md:** Do not read or attempt to process `human-notes.md`. This file is reserved for the human user's personal tracking and notes; it is not intended for agent consumption.
- **Contextual Awareness:** Maintain awareness of previous prompt executions and their side effects on the codebase while adhering to the self-contained nature of new prompt files.

## Session Assumption
- Each file in `.prompts/PROMPT_XX.txt` is intended to be executed in a **fresh coding assistant session** (e.g., Gemini, Codex, Claude).
- Prompts must be self-contained and not rely on previous context, even if they build upon the state left by a previous prompt.

## Environment & Python
- **Use `uv`:** Always use `uv` for creating virtual environments and managing dependencies.
- **Python Version:** When creating a virtual environment via `uv`, you MUST explicitly specify the Python version (e.g., `uv venv --python 3.12`).

## Documentation & Style
- **Freshness & Usefulness:** Maintain `src/README.md` as the authoritative, up-to-date guide for codebase architecture, schema details, and operational commands. Documentation must be actionable and reflect the current state of the system.
- **Audit Authority:** `data/reports/dark_matter_todo.json` is the authoritative source for identifying missing profiles (languages, concepts, organizations) that need to be implemented in the next phase.
- **Data Completeness:** Any new language entry added to `data/languages.json` MUST be accompanied by a corresponding detailed JSON profile in `data/docs/language_profiles/`. Any new significant concept (e.g., added to a person's contributions or a language's key innovations) MUST be accompanied by a corresponding detailed JSON profile in `data/docs/concept_profiles/`. The profiles must include fields for `title`, `overview`, `historical_context`, `mental_model`, `key_innovations` (or `key_aspects`), `tradeoffs`, `legacy`, and `ai_assisted_discovery_missions`.
- **Visual Hygiene:** Do not use emojis in section titles or documentation headers.
- **Typography:** Avoid using em dashes (—) or regular dashes (-) in place of em dashes in documentation. Use standard punctuation or clear sentence structures instead.
- **Actionable Examples:** Prefer `uv run` in documentation examples to ensure consistent environment execution.

## Commit Style
- **Prefix:** Use `[PROMPT_XX]` for changes related to a specific prompt file (e.g., `[PROMPT_01]`). Use `[PRE-FLIGHT {CATEGORY}]` for architectural or pre-run refinements.
- **Format:** Tim Pope style (Multi-line).
  - **Subject:** 50 characters or less, capitalized, no period.
  - **Body:** Separated from the subject by a blank line, wrapped at 72-80 characters.
  - **Content:** Detail the *rationale* and *technical impact* of the changes. Avoid listing every file if the grouping is logical.
- **No Co-author:** Do not include co-author sections in commit messages.
- **Grouped Changes:** Perform logical, surgical updates and commit them individually. Group files or hunks that share a conceptual purpose (e.g., updating existing cross-references vs. adding new data) into separate, descriptive commits.
