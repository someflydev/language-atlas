.PHONY: init build server audit dark-matter test harden type-check test-intensive docs site pages clean help

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  init            Set up virtualenv, install deps, and build the database"
	@echo "  build           Rebuild the SQLite database from JSON sources"
	@echo "  server          Start the FastAPI dev server on port 8084"
	@echo "  audit           Run the Atlas Auditor to check data integrity"
	@echo "  dark-matter     Run the Dark Matter audit to find missing content"
	@echo "  test            Run the comprehensive test suite"
	@echo "  harden          Run full reliability suite (type-check, audit, test)"
	@echo "  type-check      Run mypy type checking"
	@echo "  test-intensive  Run long-running analytical tests"
	@echo "  docs            Generate Markdown documentation from the SQLite database"
	@echo "  site            Export fully-rendered static HTML site into site/"
	@echo "  pages           Prepare gh-pages artifacts (run on gh-pages branch only)"
	@echo "  clean           Remove generated artifacts"

init:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not on PATH. Install it from https://github.com/astral-sh/uv"; exit 1; }
	uv venv --python 3.12
	uv sync
	$(MAKE) build

build:
	@echo "Building SQLite database..."
	PYTHONPATH=src uv run python -m app.core.build_sqlite

server:
	@echo "Starting FastAPI dev server on port 8084..."
	PYTHONPATH=src uv run uvicorn app.app:app --reload --reload-dir src/app --port 8084

audit:
	@echo "Running Atlas Auditor..."
	PYTHONPATH=src uv run python -m app.core.auditor

dark-matter:
	@echo "Auditing for Dark Matter..."
	python3 scripts/dark_matter_audit.py

test:
	@echo "Running tests..."
	uv run pytest -v --cov=src/app/core

harden: type-check audit test
	@echo "Hardening suite complete."

type-check:
	@echo "Running type checks..."
	uv run mypy . --config-file mypy.ini

test-intensive:
	@echo "Running intensive tests..."
	uv run pytest -m intensive

docs:
	@echo "Generating documentation (INDEX.md and README.md included)..."
	PYTHONPATH=src uv run python -m app.core.site_builder

site:
	@echo "Building static site into site/..."
	PYTHONPATH=src uv run python -m app.core.site_builder --html

pages: build site
	@echo "Preparing GitHub Pages artifacts..."
	python3 scripts/prep_pages.py

clean:
	@echo "Cleaning up generated documentation and build artifacts..."
	rm -rf generated-docs/
	rm -rf dist/
	rm -rf build_temp/
	rm -rf .pytest_cache/
	rm -f atlas.spec
	rm -f language_atlas.sqlite
	rm -f .coverage
	rm -rf htmlcov/
	rm -rf site/
	# Remove generated report files; dark_matter_todo.json is tracked and recreated by make dark-matter
	rm -f generated-reports/cluster_genealogy.json
	rm -f generated-reports/creator_impact.json
	rm -f generated-reports/db_health.json
	rm -f generated-reports/innovation_trends.json
	rm -f generated-reports/safety_complexity_trends.json
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
