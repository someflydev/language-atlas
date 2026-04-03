# Agent Preferences

## Protocol
- **Load First:** Always read `AGENT.md` before executing any instructions from `.prompts/PROMPT_XX.txt` or any other directive. This ensures all architectural and stylistic mandates are followed.
- **Ignore human-notes.md:** Do not read or attempt to process `human-notes.md`. This file is reserved for the human user's personal tracking and notes; it is not intended for agent consumption.
- **Contextual Awareness:** Maintain awareness of previous prompt executions and their side effects on the codebase while adhering to the self-contained nature of new prompt files.

## Session Assumption
- Each file in `.prompts/PROMPT_XX.txt` is intended to be executed in a **fresh coding assistant session** (e.g., Gemini, Codex, Claude).
- Prompts must be self-contained and not rely on previous context, even if they build upon the state left by a previous prompt.

## Commit Style
- **Prefix:** Use `[PROMPT_XX]` for changes related to a specific prompt file (e.g., `[PROMPT_01]`). Use `[PRE-FLIGHT {CATEGORY}]` for architectural or pre-run refinements.
- **Format:** Tim Pope style (Multi-line).
  - **Subject:** 50 characters or less, capitalized, no period.
  - **Body:** Separated from the subject by a blank line, wrapped at 72-80 characters.
  - **Content:** Detail the *rationale* and *technical impact* of the changes. Avoid listing every file if the grouping is logical.
- **No Co-author:** Do not include co-author sections in commit messages.
- **Grouped Changes:** Perform logical, surgical updates and commit them individually. Group files or hunks that share a conceptual purpose (e.g., updating existing cross-references vs. adding new data) into separate, descriptive commits.
