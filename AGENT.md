# Agent Preferences

## Session Assumption
- Each file in `.prompts/PROMPT_XX.txt` is intended to be executed in a **fresh coding assistant session** (e.g., Gemini, Codex, Claude).
- Prompts must be self-contained and not rely on previous context, even if they build upon the state left by a previous prompt.

## Commit Style
- **Prefix:** Use `[PROMPT_XX]` for changes related to a specific prompt file. Use `[PRE-FLIGHT {CATEGORY}]` for architectural or pre-run refinements.
- **Format:** Tim Pope style (Subject line, followed by a blank line and a descriptive body).
- **Line Length:** Body lines must not exceed 80 characters.
- **No Co-author:** Do not include co-author sections in commit messages.
- **Grouped Changes:** Perform surgical updates and commit them individually to avoid the need for interactive staging (`git add -p`) where possible.
