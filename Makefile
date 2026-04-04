.PHONY: docs clean help

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  docs   Generate Markdown documentation from the SQLite database"
	@echo "  clean  Remove the generated documentation"

docs:
	@echo "Generating documentation..."
	python3 scripts/generate_docs.py

clean:
	@echo "Cleaning up generated documentation..."
	rm -rf generated-docs/
