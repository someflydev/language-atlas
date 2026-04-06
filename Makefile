.PHONY: docs clean help test test-intensive build audit dark-matter type-check harden

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  docs            Generate Markdown documentation from the SQLite database"
	@echo "  build           Rebuild the SQLite database from JSON sources"
	@echo "  audit           Run the Atlas Auditor to check data integrity"
	@echo "  dark-matter     Run the Dark Matter audit to find missing content"
	@echo "  test            Run the comprehensive test suite"
	@echo "  test-intensive  Run long-running analytical tests"
	@echo "  type-check      Run mypy type checking"
	@echo "  harden          Run full reliability suite (type-check, audit, test)"
	@echo "  clean           Remove generated artifacts"

docs:
	@echo "Generating documentation..."
	python3 scripts/generate_docs.py

build:
	@echo "Building SQLite database..."
	python3 src/app/core/build_sqlite.py

audit:
	@echo "Running Atlas Auditor..."
	python3 src/app/core/auditor.py

dark-matter:
	@echo "Auditing for Dark Matter..."
	python3 scripts/dark_matter_audit.py

type-check:
	@echo "Running type checks..."
	mypy . --config-file mypy.ini

test:
	@echo "Running tests..."
	pytest -v --cov=src/app/core

test-intensive:
	@echo "Running intensive tests..."
	pytest -m intensive

harden: type-check audit test
	@echo "Hardening suite complete."

clean:
	@echo "Cleaning up generated documentation and build artifacts..."
	rm -rf generated-docs/
	rm -rf dist/
	rm -rf build_temp/
	rm -rf .pytest_cache/
	rm -f data/reports/historical_insights.json
