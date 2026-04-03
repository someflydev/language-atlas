# Agent Preferences

## Session Assumption
- Each file in `.prompts/PROMPT_XX.txt` is intended to be executed in a **fresh coding assistant session** (e.g., Gemini, Codex, Claude).
- Prompts must be self-contained and not rely on previous context, even if they build upon the state left by a previous prompt.

## Commit Style
- **Prefix:** Use `[PROMPT_XX]` for changes related to a specific prompt file (e.g., `[PROMPT_01]`). Use `[PRE-FLIGHT {CATEGORY}]` for architectural or pre-run refinements.
- **Format:** Tim Pope style.
  - **Subject:** 50 characters or less, capitalized, no period.
  - **Body:** Separated by a blank line, wrapped at 72-80 characters.
  - **Content:** Explain the *why* and *what* of the change.
- **No Co-author:** Do not include co-author sections in commit messages.
- **Grouped Changes:** Perform logical, surgical updates and commit them individually. Group files that share a conceptual purpose (e.g., schema vs. data) into separate commits.
