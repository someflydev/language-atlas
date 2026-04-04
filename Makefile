.PHONY: docs clean help test test-intensive

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  docs            Generate Markdown documentation from the SQLite database"
	@echo "  test            Run fast tests (unit and consistency checks)"
	@echo "  test-intensive  Run intensive analytical tests and regenerate insight reports"
	@echo "  clean           Remove the generated documentation and test artifacts"

docs:
	@echo "Generating documentation..."
	USE_SQLITE=1 uv run python3 scripts/generate_docs.py

test:
	@echo "Running fast tests..."
	uv run pytest -m "not intensive"

test-intensive:
	@echo "Running intensive analytical tests..."
	uv run pytest -m intensive
	@echo "Regenerating historical insights..."
	uv run python3 src/app/core/insights.py

clean:
	@echo "Cleaning up generated documentation..."
	rm -rf generated-docs/
	rm -rf .pytest_cache/
	rm -f data/reports/historical_insights.json
