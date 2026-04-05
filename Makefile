.PHONY: docs clean help test test-intensive build audit dark-matter

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  docs            Generate Markdown documentation from the SQLite database"
	@echo "  test            Run fast tests (unit, consistency, and auditor checks)"
	@echo "  test-intensive  Run intensive analytical tests and regenerate insight reports"
	@echo "  build           Build the standalone Zenith binary (dist/atlas)"
	@echo "  audit           Run the Atlas Auditor (Validation 2.0) checks"
	@echo "  dark-matter     Run the Dark Matter Audit to identify missing profiles"
	@echo "  server          Start the FastAPI web server on port 8084"
	@echo "  clean           Remove the generated documentation and test artifacts"

docs:
	@echo "Generating documentation..."
	USE_SQLITE=1 uv run python3 scripts/generate_docs.py

test:
	@echo "Running fast tests..."
	uv run pytest -m "not intensive"

audit:
	@echo "Running Atlas Auditor checks..."
	uv run python3 src/app/core/auditor.py

dark-matter:
	@echo "Running Dark Matter Audit..."
	uv run python3 scripts/dark_matter_audit.py

server:
	@echo "Starting Language Atlas server on http://localhost:8084..."
	@echo "Press Ctrl+C to stop."
	cd src/app && USE_SQLITE=1 uv run uvicorn app:app --host 0.0.0.0 --port 8084

build:
	@echo "Building Zenith standalone binary..."
	uv run python3 scripts/build_zenith.py

test-intensive:
	@echo "Running intensive analytical tests..."
	uv run pytest -m intensive
	@echo "Regenerating historical insights..."
	uv run python3 src/app/core/insights.py

clean:
	@echo "Cleaning up generated documentation and build artifacts..."
	rm -rf generated-docs/
	rm -rf dist/
	rm -rf build_temp/
	rm -rf .pytest_cache/
	rm -f data/reports/historical_insights.json
