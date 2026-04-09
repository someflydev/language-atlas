# Language Atlas — CLAUDE.md

Language Atlas is a data-driven research platform for exploring the history and evolution of programming languages. It ships as a FastAPI web app, Typer CLI, and Textual TUI, all backed by a SQLite database built from JSON source files.

## Read First
Always read `AGENT.md` before executing any `.prompts/PROMPT_XX.txt` file.

## Context Files (load what you need)
| File | Load when... |
|---|---|
| `.context/architecture.md` | Understanding overall stack, data flow, layers |
| `.context/database.md` | Working with schema, tables, views, CTEs |
| `.context/routes.md` | Adding/changing routes, templates, or API endpoints |
| `.context/data-pipeline.md` | Editing JSON data, profile docs, or build pipeline |
| `.context/commands.md` | Running the server, tests, CLI, scripts |
| `.context/workflow.md` | Starting a prompt session, committing, handoffs |

## Session Checklist
When starting a new PROMPT session:
1. Load relevant context files above
2. Create `tmp/PROMPT_XX_checklist.md` with `- [ ]` checkboxes
3. Check off work as it's done
4. If session ends unfinished, write `tmp/HANDOFF.md` (never commit it)

## Key Paths
```
src/app/app.py              FastAPI app (all routes)
src/app/core/data_loader.py DataLoader — SQLite/JSON unified access
src/app/core/build_sqlite.py JSON → SQLite pipeline
src/app/core/auditor.py     Data integrity auditor
src/app/core/insights.py    InsightGenerator (analytical CTEs)
src/app/templates/          Jinja2 templates
src/cli.py                  Typer CLI
src/tui.py                  Textual TUI
data/                       JSON source of truth
data/docs/                  Narrative profile JSON files
language_atlas.sqlite       Built artifact (gitignored)
AGENT.md                    Mandate file — read before any prompt
API_GUIDE.md                All public endpoints
src/README.md               Architecture reference
```

## Common Operations
```bash
make build        # Rebuild SQLite from JSON
make test         # Run test suite
make harden       # type-check + audit + test
make docs         # Regenerate generated-docs/
make audit        # Data integrity check
make dark-matter  # Find missing profiles
```

## Commit Style (Tim Pope, heredoc)
- Prefix: `[PROMPT_XX]`; body at 72-80 chars; no co-author
- Never `git add .` — stage files explicitly
- See `context/workflow.md` for full rules
