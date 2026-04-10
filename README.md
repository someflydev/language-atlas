# Language Atlas

<!-- TODO copy -->
Language Atlas is a research platform for exploring the history,
evolution, and intellectual lineage of programming languages. It ships
as a FastAPI web app, a Typer CLI, and a Textual TUI, all backed by a
SQLite database compiled from a curated JSON corpus.

## Quickstart

```bash
make init
make server
```

Open http://localhost:8084.

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

## Live demo

<!-- TODO live URL -->
A static export with a client-side SQLite database is published from
the `gh-pages` branch. See [`docs/GH_PAGES.md`](docs/GH_PAGES.md) for
the build and deploy workflow.

## License

<!-- TODO license -->
