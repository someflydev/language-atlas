# Agent Preferences

## Protocol
- **Load First:** Always read `AGENT.md` before executing any instructions from `.prompts/PROMPT_XX.txt` or any other directive. This ensures all architectural and stylistic mandates are followed.
- **Ignore human-notes.md:** Do not read or attempt to process `human-notes.md`. This file is reserved for the human user's personal tracking and notes; it is not intended for agent consumption.
- **Contextual Awareness:** Maintain awareness of previous prompt executions and their side effects on the codebase while adhering to the self-contained nature of new prompt files.
- **Use neutral playbooks when relevant:** Check `.context/agent-playbooks/` for reusable, agent-agnostic workflows before inventing a new process for dark matter curation or content-completeness prompt planning.

## Session Assumption
- Each file in `.prompts/PROMPT_XX.txt` is intended to be executed in a **fresh coding assistant session** (e.g., Gemini, Codex, Claude).
- Prompts must be self-contained and not rely on previous context, even if they build upon the state left by a previous prompt.

## Environment & Python
- **Use `uv`:** Always use `uv` for creating virtual environments and managing dependencies.
- **Python Version:** When creating a virtual environment via `uv`, you MUST explicitly specify the Python version (e.g., `uv venv --python 3.12`).

## Documentation & Style
- **Freshness & Usefulness:** Maintain `src/README.md` as the authoritative, up-to-date guide for codebase architecture, schema details, and operational commands. Documentation must be actionable and reflect the current state of the system.
- **API Authority:** Maintain `API_GUIDE.md` as the comprehensive reference for all public endpoints. If the API is updated, this file MUST be updated to reflect changes.
- **Audit Authority:** `generated-reports/dark_matter_todo.json` is the authoritative source for identifying missing profiles (languages, concepts, organizations, historical events) that need to be implemented in the next phase. This file SHOULD be committed alongside any logic changes to `scripts/dark_matter_audit.py` to ensure the report reflects the latest discovery heuristics.
- **Data Completeness:**
  - **Language Profiles:** Every language in `data/languages.json` MUST have a profile in `data/docs/language_profiles/`. Required fields: `title`, `overview`, `historical_context`, `mental_model`, `key_innovations`, `tradeoffs`, `legacy`, `ai_assisted_discovery_missions`.
  - **Concept Profiles:** Significant concepts (innovations, paradigms, mental models) MUST have a profile in `data/docs/concept_profiles/`. Required fields: `title`, `overview`, `historical_context`, `key_aspects`, `technical_implications`, `legacy`, `ai_assisted_discovery_missions`.
  - **Historical Events:** Significant events (e.g., WWII, Garmisch Conference) MUST have a profile in `data/docs/historical_events/`. Required fields: `title`, `date`, `overview`, `impact_on_computing`, `key_figures`, `legacy`, `ai_assisted_discovery_missions`.
  - **People Profiles:** Every person in `data/people.json` SHOULD have a profile in `data/docs/people_profiles/`. Required fields: `title`, `overview`, `historical_context`, `pivotal_works`, `affiliations`, `legacy`, `ai_assisted_discovery_missions`. If they pioneered a specific mental model (e.g., Dijkstra and Structured Programming), include a `mental_model` section.
    - **Filename mapping:** Replace spaces with underscores, preserve punctuation from the canonical person name, and transliterate non-ASCII letters to the closest reasonable ASCII form. The filename stem must map back to the canonical `data/people.json` name after underscore-to-space conversion and ASCII transliteration. Examples: `Friedrich L. Bauer` -> `Friedrich_L._Bauer.json`; `José Valim` -> `Jose_Valim.json`.
  - **Organization Profiles:** Major organizations MUST have a profile in `data/docs/org_profiles/`. Required fields: `title`, `founded`, `overview`, `key_contributions`, `pivotal_people`, `legacy`, `ai_assisted_discovery_missions`.
  - **Atlas Meta Profiles:** Profiles describing the internal architecture of the Language Atlas itself (e.g., The Pedagogical Engine, Zenith State) MUST have a profile in `data/docs/atlas_meta/`.
  - **Era Summaries & Crossroads:** These narrative files in `data/docs/era_summaries/` and `data/docs/crossroads/` act as hubs. They must link to the detailed profiles mentioned above.
- **Visual Hygiene:** Do not use emojis in section titles or documentation headers.
- **Typography:** Avoid using em dashes (—) or regular dashes (-) in place of em dashes in documentation. Use standard punctuation or clear sentence structures instead.
- **Actionable Examples:** Prefer `uv run` in documentation examples to ensure consistent environment execution.

## Commit Style
- **Prefix:** Use `[PROMPT_XX]` for changes related to a specific prompt file (e.g., `[PROMPT_01]`). Use `[PRE-FLIGHT {CATEGORY}]` for architectural or pre-run refinements.
- **Format:** Tim Pope style (Multi-line).
  - **Subject:** 50 characters or less, capitalized, no period.
  - **Body:** Separated from the subject by a blank line, wrapped at 72-80 characters.
  - **Content:** Detail the *rationale* and *technical impact* of the changes. Avoid listing every file if the grouping is logical.
- **Use heredoc:** Ensure there are no raw \n in commit strings (i.e. `git commit -m "$(cat <<'EOF' ... EOF)"`
- **No Co-author:** Do not include co-author sections in commit messages.
- **Explicit Staging:** NEVER lazily use `git add .` or `git commit -a`. Explicitly stage only the necessary and modified tracked files for each commit using `git add <file>...`. This prevents untracked or personal files (like `human-notes.md` or `HANDOFF.md`) from being accidentally committed. DO NOT commit `HANDOFF.md` when it is written; it should remain untracked.
- **Grouped Changes:** Perform logical, surgical updates and commit them individually. Group files or hunks that share a conceptual purpose (e.g., updating existing cross-references vs. adding new data) into separate, descriptive commits.
