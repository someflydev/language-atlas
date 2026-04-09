"""Static-site Markdown builder for Language Atlas.

Orchestrates all Markdown generation for generated-docs/. Logic lives here;
scripts/generate_docs.py is a thin CLI wrapper that calls build_markdown().

Output today is Markdown only. HTML rendering is added in PROMPT_50.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from app.core.data_loader import DataLoader


class SiteBuilder:
    """Generates the generated-docs/ Markdown tree from a DataLoader instance.

    All data access goes through the DataLoader; no raw SQL appears here.
    Trivial composition (grouping, sorting, slicing) is done inline.
    """

    def __init__(self, loader: DataLoader, out_dir: Path) -> None:
        self._loader = loader
        self._out = out_dir

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def build_markdown(self) -> None:
        """Orchestrate full Markdown generation into out_dir."""
        self._setup_dirs()
        print("Generating language profiles...")
        self.emit_language_profiles()
        print("Generating concept profiles...")
        self.emit_concept_profiles()
        print("Generating era summaries...")
        self.emit_era_summaries()
        print("Generating thematic documents...")
        self.emit_thematic_docs()
        print("Generating index files...")
        self.emit_paradigm_index()
        self.emit_era_index()
        print("Generating homepage and meta pages...")
        self.emit_narrative_overview()
        self.emit_homepage_index()

    def _setup_dirs(self) -> None:
        for sub in ("languages", "eras", "paradigms", "concepts"):
            (self._out / sub).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Language profiles
    # ------------------------------------------------------------------

    def emit_language_profiles(self) -> None:
        """Write one Markdown file per language into languages/."""
        for lang_stub in self._loader.get_all_languages():
            info = self._loader.get_language_doc_info(lang_stub['name'])
            if info is None:
                continue

            display_name: str = info.get('display_name') or info['name']
            profile_title: str = info.get('profile_title') or display_name

            paradigms: List[str] = info.get('paradigms') or []
            creators: List[str] = info.get('creators') or []

            frontmatter: Dict[str, Any] = {
                "title": display_name,
                "year": info.get('year'),
                "cluster": info.get('cluster'),
                "generation": info.get('generation'),
                "paradigms": paradigms,
                "creators": creators,
                "is_keystone": bool(info.get('is_keystone')),
                "typing_discipline": info.get('typing_discipline'),
                "memory_management": info.get('memory_management'),
                "safety_model": info.get('safety_model'),
            }

            safe_name = info['name'].replace(" ", "_").replace("/", "_")
            file_path = self._out / "languages" / f"{safe_name}.md"

            influenced_by: List[str] = info.get('influenced_by') or []
            influenced: List[str] = info.get('influenced') or []
            sections: List[Dict[str, Any]] = info.get('sections') or []

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("---\n")
                f.write(json.dumps(frontmatter, indent=2))
                f.write("\n---\n\n")
                f.write(f"# {profile_title}\n\n")

                if info.get('profile_overview'):
                    f.write(f"{info['profile_overview']}\n\n")

                f.write(f"## Philosophy\n{info.get('philosophy', '')}\n\n")
                f.write(f"## Mental Model\n{info.get('mental_model', '')}\n\n")

                if sections:
                    for section in sections:
                        title = section["section_name"].replace("_", " ").title()
                        f.write(f"## {title}\n{section['content']}\n\n")

                f.write("## Relationships\n")
                if influenced_by:
                    f.write(f"- **Influenced by:** {', '.join(influenced_by)}\n")
                if influenced:
                    f.write(f"- **Influenced:** {', '.join(influenced)}\n")
                if not influenced_by and not influenced:
                    f.write("- No documented direct influences.\n")
                f.write("\n")

                f.write("## Technical Details\n")
                f.write(f"- **Typing:** {info.get('typing_discipline')}\n")
                f.write(
                    f"- **Memory Management:** {info.get('memory_management')}\n"
                )
                f.write(f"- **Safety Model:** {info.get('safety_model')}\n")
                f.write(f"- **Complexity Bias:** {info.get('complexity_bias')}\n")

    # ------------------------------------------------------------------
    # Concept profiles
    # ------------------------------------------------------------------

    def emit_concept_profiles(self) -> None:
        """Write one Markdown file per concept into concepts/."""
        for concept_stub in self._loader.get_all_concepts():
            info = self._loader.get_concept_doc_info(concept_stub['name'])
            if info is None:
                continue

            profile_title: str = info.get('profile_title') or info['name']
            sections: List[Dict[str, Any]] = info.get('sections') or []

            safe_name = info['name'].replace(" ", "_").replace("/", "_")
            file_path = self._out / "concepts" / f"{safe_name}.md"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {profile_title}\n\n")

                if info.get('profile_overview'):
                    f.write(f"{info['profile_overview']}\n\n")

                f.write(f"## Description\n{info.get('description', '')}\n\n")

                if sections:
                    for section in sections:
                        title = section["section_name"].replace("_", " ").title()
                        f.write(f"## {title}\n{section['content']}\n\n")

    # ------------------------------------------------------------------
    # Paradigm index
    # ------------------------------------------------------------------

    def emit_paradigm_index(self) -> None:
        """Write paradigms.md listing all paradigms with their languages."""
        paradigms = self._loader.get_all_paradigm_objects()
        with open(self._out / "paradigms.md", "w", encoding="utf-8") as f:
            f.write("# Languages by Paradigm\n\n")
            for p in paradigms:
                f.write(f"## {p['name']}\n")
                desc = p.get('description') or "No description available."
                f.write(f"{desc}\n\n")

                lang_list: List[Dict[str, Any]] = p.get('lang_list') or []
                if lang_list:
                    for lang in lang_list:
                        safe_name = lang['name'].replace(" ", "_").replace("/", "_")
                        f.write(
                            f"- [{lang['display_name']}]"
                            f"(languages/{safe_name}.md)\n"
                        )
                else:
                    f.write("- No languages listed.\n")
                f.write("\n")

    # ------------------------------------------------------------------
    # Era index (by generation)
    # ------------------------------------------------------------------

    def emit_era_index(self) -> None:
        """Write eras.md grouping languages by generation."""
        all_langs = self._loader.get_all_languages()

        # Group by generation, preserving insertion order via dict
        gen_map: Dict[str, List[Dict[str, Any]]] = {}
        for lang in all_langs:
            gen = lang.get('generation')
            if not gen:
                continue
            gen_map.setdefault(gen, []).append(lang)

        # Sort generations by the earliest language year within each group
        sorted_gens = sorted(
            gen_map.keys(),
            key=lambda g: min(
                (l.get('year') or 9999) for l in gen_map[g]
            ),
        )

        with open(self._out / "eras.md", "w", encoding="utf-8") as f:
            f.write("# Languages by Era (Generation)\n\n")
            for gen in sorted_gens:
                f.write(f"## {gen.title()}\n")
                langs_in_gen = sorted(
                    gen_map[gen], key=lambda l: l.get('year') or 0
                )
                for lang in langs_in_gen:
                    safe_name = lang['name'].replace(" ", "_").replace("/", "_")
                    display = lang.get('display_name') or lang['name']
                    f.write(
                        f"- [{display}](languages/{safe_name}.md)"
                        f" ({lang.get('year')})\n"
                    )
                f.write("\n")

    # ------------------------------------------------------------------
    # Era summaries
    # ------------------------------------------------------------------

    def emit_era_summaries(self) -> None:
        """Write one Markdown file per era into eras/."""
        eras = self._loader.get_all_era_summaries()
        for era in eras:
            file_path = self._out / "eras" / f"{era['slug']}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {era['title']}\n\n")
                f.write(f"## Overview\n{era.get('overview', '')}\n\n")

                drivers: List[Dict[str, Any]] = era.get('key_drivers') or []
                if drivers:
                    f.write("## Key Drivers\n")
                    for d in drivers:
                        f.write(f"- **{d['name']}** {d.get('description', '')}\n")
                    f.write("\n")

                pivotal: List[Dict[str, Any]] = era.get('pivotal_languages') or []
                if pivotal:
                    f.write("## Pivotal Languages\n")
                    for p in pivotal:
                        f.write(f"- **{p['name']}** {p.get('description', '')}\n")
                    f.write("\n")

                f.write(f"## Legacy Impact\n{era.get('legacy_impact', '')}\n\n")
                if era.get('diagram'):
                    f.write(f"## Diagram Concept\n{era['diagram']}\n\n")

    # ------------------------------------------------------------------
    # Thematic documents
    # ------------------------------------------------------------------

    def emit_thematic_docs(self) -> None:
        """Write CROSSROADS.md, MODERN_REACTIONS.md, PARADIGM_MATRIX.md,
        TIMELINE.md, and CONCEPTS.md."""
        self._emit_crossroads()
        self._emit_modern_reactions()
        self._emit_paradigm_matrix()
        self._emit_timeline()
        self._emit_concepts_summary()

    def _emit_crossroads(self) -> None:
        crossroads = self._loader.get_crossroads()
        with open(self._out / "CROSSROADS.md", "w", encoding="utf-8") as f:
            f.write("# The Crossroads of Computing\n\n")
            for cr in crossroads:
                f.write(f"## {cr['title']}\n{cr.get('explanation', '')}\n\n")

    def _emit_modern_reactions(self) -> None:
        reactions = self._loader.get_modern_reactions()
        with open(self._out / "MODERN_REACTIONS.md", "w", encoding="utf-8") as f:
            f.write("# Modern Reactions in Language Design\n\n")
            for mr in reactions:
                f.write(f"## {mr['theme']}\n{mr.get('explanation', '')}\n\n")

    def _emit_paradigm_matrix(self) -> None:
        matrix = self._loader.get_paradigm_matrix()
        with open(self._out / "PARADIGM_MATRIX.md", "w", encoding="utf-8") as f:
            f.write("# The Paradigm Matrix: Technical Dimensions\n\n")
            for m in matrix:
                f.write(f"## {m['axis']}\n{m.get('details', '')}\n\n")

    def _emit_timeline(self) -> None:
        periods = self._loader.get_timeline_with_related()
        with open(self._out / "TIMELINE.md", "w", encoding="utf-8") as f:
            f.write("# The Chronological Atlas: Major Events\n\n")
            for p in periods:
                f.write(f"## {p['era_or_period']}\n")
                for e in p.get('events', []):
                    if e.get('year'):
                        f.write(f"- **{e['year']}:** {e.get('description', '')}\n")
                    else:
                        f.write(f"{e.get('description', '')}\n")

                    related: List[str] = e.get('related') or []
                    if related:
                        f.write(
                            f"  * [Related: {', '.join(related)}]\n"
                        )
                f.write("\n")

    def _emit_concepts_summary(self) -> None:
        concepts = self._loader.get_all_concepts()
        with open(self._out / "CONCEPTS.md", "w", encoding="utf-8") as f:
            f.write("# Core Concepts: The Soul of Computation\n\n")
            for c in concepts:
                safe_name = c['name'].replace(" ", "_").replace("/", "_")
                f.write(f"## [{c['name']}](concepts/{safe_name}.md)\n")
                f.write(f"{c.get('description', '')}\n\n")

    # ------------------------------------------------------------------
    # Narrative overview (generated-docs/README.md)
    # ------------------------------------------------------------------

    def emit_narrative_overview(self) -> None:
        """Write generated-docs/README.md: project meta and regeneration guide."""
        with open(self._out / "README.md", "w", encoding="utf-8") as f:
            f.write("# About these docs\n\n")
            f.write(
                "This directory is auto-generated from `language_atlas.sqlite`"
                " by `src/app/core/site_builder.py`. Do not hand-edit files"
                " here; they will be overwritten on the next `make docs` run.\n\n"
            )

            f.write("## Regenerating\n\n")
            f.write("```bash\n")
            f.write("make build   # rebuild language_atlas.sqlite from JSON sources\n")
            f.write("make docs    # re-run site_builder; produces INDEX.md and README.md\n")
            f.write("```\n\n")

            f.write("## Source layout\n\n")
            f.write(
                "- `data/` - JSON source of truth for all languages,"
                " paradigms, people, and concepts\n"
            )
            f.write(
                "- `data/docs/` - narrative profile JSON files"
                " (language_profiles/, concept_profiles/, era_summaries/, etc.)\n"
            )
            f.write(
                "- `src/app/core/` - build_sqlite.py, data_loader.py,"
                " site_builder.py, auditor.py, insights.py\n"
            )
            f.write(
                "- `scripts/` - thin CLI wrappers and utility scripts"
                " (generate_docs.py, dark_matter_audit.py, etc.)\n"
            )
            f.write("\n")

            f.write("## Live app\n\n")
            f.write(
                "See `src/README.md` for the full architecture guide and"
                " `API_GUIDE.md` for all public endpoints.\n\n"
            )
            f.write(
                "To run the dev server locally:\n\n"
                "```bash\n"
                "cd src/app && uv run uvicorn app:app --reload --port 8084\n"
                "```\n"
            )

    # ------------------------------------------------------------------
    # Homepage index (generated-docs/INDEX.md)
    # ------------------------------------------------------------------

    def emit_homepage_index(self) -> None:
        """Write generated-docs/INDEX.md: table of contents and highlights."""
        tagline = self._get_project_tagline()
        top_langs = self._loader.get_top_influential(10)
        eras = self._loader.get_all_era_summaries()
        counts = self._loader.get_entity_counts()

        with open(self._out / "INDEX.md", "w", encoding="utf-8") as f:
            f.write("# Language Atlas\n\n")
            f.write(f"{tagline}\n\n")

            f.write("## Browse\n\n")
            browse_links = [
                ("Eras", "eras.md"),
                ("Paradigms", "paradigms.md"),
                ("Concepts", "CONCEPTS.md"),
                ("Crossroads", "CROSSROADS.md"),
                ("Modern Reactions", "MODERN_REACTIONS.md"),
                ("Paradigm Matrix", "PARADIGM_MATRIX.md"),
                ("Timeline", "TIMELINE.md"),
            ]
            for label, target in browse_links:
                f.write(f"- [{label}]({target})\n")
            f.write("\n")

            f.write("## Highlights\n\n")
            for lang in top_langs:
                name = lang['name']
                display = lang.get('display_name') or name
                safe_name = name.replace(" ", "_").replace("/", "_")
                f.write(f"- [{display}](languages/{safe_name}.md)\n")
            f.write("\n")

            f.write("## Eras at a glance\n\n")
            for era in eras:
                slug = era.get('slug') or ''
                title = era.get('title') or slug
                f.write(f"- [{title}](eras/{slug}.md)\n")
            f.write("\n")

            f.write("## Counts\n\n")
            f.write(f"- Languages: {counts.get('languages', 0)}\n")
            f.write(f"- Paradigms: {counts.get('paradigms', 0)}\n")
            f.write(f"- Concepts: {counts.get('concepts', 0)}\n")
            f.write(f"- People: {counts.get('people', 0)}\n")
            f.write(f"- Language profiles: {counts.get('profiles', 0)}\n")
            f.write("\n")

            f.write("## Where to go next\n\n")
            f.write(
                "See [README.md](README.md) for how these docs are generated"
                " and how to regenerate them. To explore the Atlas interactively,"
                " run the FastAPI dev server on port 8084 locally:\n\n"
                "```bash\n"
                "cd src/app && uv run uvicorn app:app --reload --port 8084\n"
                "```\n"
            )

    def _get_project_tagline(self) -> str:
        """Return a one-paragraph tagline from atlas_meta, or a placeholder."""
        meta_dir = Path(self._loader.data_dir) / "docs" / "atlas_meta"
        candidates = [
            meta_dir / "language_atlas.json",
            meta_dir / "atlas_overview.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                try:
                    data = json.loads(candidate.read_text(encoding="utf-8"))
                    if data.get("overview"):
                        return str(data["overview"])
                except Exception:
                    pass

        return (
            "Language Atlas is a data-driven research platform for exploring"
            " the history and evolution of programming languages."
            " <!-- TODO copy -->"
        )
