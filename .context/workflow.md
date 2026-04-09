# Workflow: Prompts, Sessions & Commits

## Session Model
- Each `.prompts/PROMPT_XX.txt` file is ONE self-contained coding session
- Sessions are designed fresh (no cross-session memory reliance)
- Commits are prefixed `[PROMPT_XX]` to match the prompt file number
- AGENT.md must be read first before executing any PROMPT file

## Starting a New PROMPT Session
1. Read `AGENT.md` and `CLAUDE.md`
2. Load relevant `context/` files for the work at hand
3. Create `tmp/PROMPT_XX_checklist.md` with `- [ ]` markdown checkboxes for all planned work
4. Work through the checklist, checking off items as completed
5. If session ends before work is complete, write `tmp/HANDOFF.md` (never commit it)

## Checklist File Convention
```
tmp/PROMPT_XX_checklist.md
- [ ] Step one description
- [ ] Step two description
- [x] Completed step
```

## Handoff File Convention
```
tmp/HANDOFF.md
# Handoff for PROMPT_XX
## Completed
- What was done
## Remaining
- What still needs doing
## Context
- Any gotchas or state to know
```
(Written to tmp/, never committed)

## Commit Hygiene
- **Style:** Tim Pope multi-line via heredoc (NO raw \n in commit string)
- **Subject:** 50 chars max, capitalized, no trailing period
- **Body:** Blank line after subject, wrapped at 72-80 chars, explain WHY
- **No co-author lines**
- **Prefixes:**
  - `[PROMPT_XX]` — primary work for that prompt file
  - `[PROMPT_XX extra]` — handoff/follow-up work before next planned prompt
  - `[Add CLAUDE.md]`, `[PRE-FLIGHT {CATEGORY}]` — meta commits

## Staging Rules
- NEVER `git add .` or `git add -A`
- Always stage specific files: `git add src/app/app.py data/languages.json`
- Never commit: `human-notes.md`, `tmp/HANDOFF.md`, `tmp/*.md`, `*.sqlite`, `generated-docs/`, `generated-reports/` (unless explicitly tracking changes to `dark_matter_todo.json`)

## Commit Grouping
Group related files into logical commits:
- Data changes (JSON files) separate from code changes
- Template changes separate from backend logic
- Test changes can be grouped with the feature they test

## Heredoc Commit Pattern
```bash
git commit -m "$(cat <<'EOF'
[PROMPT_XX] Subject line here

Body explaining rationale and technical impact,
wrapped at 72-80 characters per line.
EOF
)"
```

## Key Docs to Keep Updated
- `src/README.md` — authoritative codebase guide (keep current)
- `API_GUIDE.md` — update whenever routes change
- `generated-reports/dark_matter_todo.json` — commit alongside `dark_matter_audit.py` changes
