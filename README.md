# Language Atlas

Language Atlas is a research platform for exploring the history,
evolution, and intellectual lineage of programming languages. It ships
as a FastAPI web app, a Typer CLI, and a Textual TUI, all backed by a
SQLite database compiled from a curated JSON corpus.

The Atlas answers questions like: What influenced Rust? Who invented
ML? Which languages share a paradigm? How did systems programming
evolve from the 1960s to today? It is aimed at language historians,
educators, and anyone curious about the ideas that shaped computing.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package and environment manager)
- Python 3.12

If `uv` is not installed, `make init` will print an install URL and exit.

## Quickstart

```bash
make init
make server
```

Open http://localhost:8084. The server runs on port 8084 by default.

`make init` sets up the virtualenv, installs dependencies, and builds
`language_atlas.sqlite` from the JSON source files. You must run it
(or `make build`) before starting the server.

## What's inside

- [`src/README.md`](src/README.md) - Architecture, layers, and data flow
- [`API_GUIDE.md`](API_GUIDE.md) - All HTTP endpoints and response shapes
- [`scripts/README.md`](scripts/README.md) - Operational scripts reference
- [`data/`](data/) - JSON source of truth (languages, paradigms, people, etc.)
- [`data/docs/`](data/docs/) - Narrative profiles (languages, concepts, eras, orgs, people)
- [`AGENT.md`](AGENT.md) - Contributor mandates; read before executing any prompt

## Make targets

| Target | Description |
|---|---|
| `make init` | Set up virtualenv, install deps, and build the database |
| `make build` | Rebuild `language_atlas.sqlite` from JSON sources |
| `make server` | Start the FastAPI dev server on port 8084 |
| `make audit` | Run the Atlas Auditor to check data integrity |
| `make dark-matter` | Find missing profiles; writes `generated-reports/dark_matter_todo.json` (tracked in git) |
| `make test` | Run the test suite |
| `make harden` | Full reliability suite: type-check, audit, test |
| `make docs` | Regenerate `generated-docs/` Markdown tree |
| `make site` | Export fully-rendered static HTML into `site/` |
| `make pages` | Prepare gh-pages artifacts (run on gh-pages branch only) |
| `make clean` | Remove generated artifacts |

## Development workflow

Content and features are added through numbered prompt files in
`.prompts/` (e.g., `PROMPT_01.txt`, `PROMPT_42.txt`). Each file is a
self-contained instruction set executed in a fresh AI coding session.
They function as a structured development journal: the sequence of
prompt files is the history of how the Atlas was built. See
[`AGENT.md`](AGENT.md) for the full contributor protocol.

## Troubleshooting

**"CRITICAL: Database not found"** on server start: run `make build`
to create `language_atlas.sqlite`.

**Port 8084 already in use**: kill the existing process or run
`PYTHONPATH=src uv run uvicorn app.app:app --port 9000` to use a
different port.

**`uv` not found**: install from https://docs.astral.sh/uv/ then
re-run `make init`.

**Python version mismatch**: `make init` pins to Python 3.12 via
`uv venv --python 3.12`. `uv` will download Python 3.12 automatically
if it is not already installed.

## Live demo

A static export with a client-side SQLite database is published from
the `gh-pages` branch. See [`GH_PAGES.md`](GH_PAGES.md) for
the build and deploy workflow.
