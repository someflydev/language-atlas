"""Static-site builder for Language Atlas.

Provides two output modes:
- SiteBuilder: Markdown generation into generated-docs/ (Markdown mode).
- SiteCrawler: Full-rendered HTML export into site/ via FastAPI TestClient
  (HTML mode, added in PROMPT_50).

The __main__ block below dispatches between the two modes:
run without --html for Markdown (make docs), with --html for HTML (make site).
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
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

    @staticmethod
    def _safe_doc_name(name: str) -> str:
        """Keep generated Markdown filenames stable without collapsing slashes."""
        return name.replace("/", "_slash_").replace(" ", "_")

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

            safe_name = self._safe_doc_name(info['name'])
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

            safe_name = self._safe_doc_name(info['name'])
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
                        safe_name = self._safe_doc_name(lang['name'])
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
                    safe_name = self._safe_doc_name(lang['name'])
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
                safe_name = self._safe_doc_name(c['name'])
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
                " (language_profiles/, concept_profiles/, etc.)\n"
            )
            f.write(
                "- `src/app/core/` - build_sqlite.py, data_loader.py,"
                " site_builder.py, auditor.py, insights.py\n"
            )
            f.write(
                "- `scripts/` - utility scripts"
                " (dark_matter_audit.py, generate_reports.py, etc.)\n"
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
                "make server\n"
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
                safe_name = self._safe_doc_name(name)
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
                "make server\n"
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


# ---------------------------------------------------------------------------
# CrawlReport
# ---------------------------------------------------------------------------

@dataclass
class CrawlReport:
    """Summary produced by SiteCrawler.crawl()."""

    written: List[str] = field(default_factory=list)
    failures: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def ok_count(self) -> int:
        return len(self.written)

    @property
    def fail_count(self) -> int:
        return len(self.failures)


# ---------------------------------------------------------------------------
# SiteCrawler
# ---------------------------------------------------------------------------

class SiteCrawler:
    """Crawls the live FastAPI app via TestClient and writes static HTML.

    Each GET route that returns HTML is fetched and written to
    site/<path>/index.html so the tree can be served as a static site.
    Internal links are rewritten from absolute (/language/C) to relative
    (../../language/C/index.html) so every page works without a server.

    URL rewriting uses focused regex passes over href="..." and src="..."
    attributes rather than pulling in a heavy dependency like BeautifulSoup4.
    This is intentional: the templates use well-formed, predictable href
    patterns, so a targeted regex is cheaper and has no extra install cost.
    The trade-off is that malformed or dynamically generated attribute values
    may not be caught; that is acceptable for this controlled codebase.
    """

    # Routes that produce JSON or are stateful; always skip these.
    _SKIP_PREFIXES = (
        "/api",
        "/compare/add",
        "/compare/remove",
        "/compare/clear",
        "/compare/tray",
        "/search",
    )

    def __init__(self, loader: DataLoader, out_dir: Path) -> None:
        self._loader = loader
        self._out = out_dir

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def crawl(self) -> CrawlReport:
        """Run the full crawl and return a CrawlReport.

        The crawl runs in two phases:
        1. Fetch all URLs and write raw HTML to disk.  Only server errors
           (5xx) are added to CrawlReport.failures; 404s are silently
           skipped since many entities have no profile page yet.
        2. Post-process every written file: rewrite absolute internal hrefs
           to relative paths, using the set of files written in phase 1.
           Any link whose target was not written (404, excluded route, or
           unsafe URL segment) is replaced with href="#" so the static site
           contains no broken internal links.
        """
        report = CrawlReport()

        os.environ["ATLAS_STATIC_MODE"] = "1"
        os.environ.setdefault("USE_SQLITE", "1")

        try:
            # Lazy import so env vars are set before app module executes.
            # app.py imports from the `app.*` package, so keeping `src`
            # on sys.path is sufficient. We append (not insert at 0) so
            # the existing `src` entry stays highest-priority.
            import sys
            app_dir = str(Path(__file__).parent.parent)
            if app_dir not in sys.path:
                sys.path.append(app_dir)

            from starlette.testclient import TestClient
            from app.app import app

            self._out.mkdir(parents=True, exist_ok=True)

            # Phase 1: fetch and write raw HTML (no link rewriting yet).
            url_to_path: Dict[str, Path] = {}
            with TestClient(app, raise_server_exceptions=False) as client:
                urls = self._enumerate_urls()
                for url in urls:
                    try:
                        status, html = self._fetch(client, url)
                        if status == 200:
                            path = self._write(url, html)
                            url_to_path[url] = path
                            report.written.append(str(path))
                        elif status >= 500:
                            report.failures.append({
                                "url": url,
                                "error": f"HTTP {status}",
                            })
                        # 404 and other 4xx: expected for entities without
                        # profiles; silently skip, do not add to failures.
                    except Exception as exc:
                        report.failures.append({"url": url, "error": str(exc)})

            self._copy_static_assets()

            # Phase 2: rewrite links with knowledge of which files exist.
            written_files = {Path(p).resolve() for p in report.written}
            for url, path in url_to_path.items():
                raw = path.read_text(encoding="utf-8")
                rewritten = self._rewrite_links(
                    raw, url, self._out, written_files
                )
                path.write_text(rewritten, encoding="utf-8")

        finally:
            os.environ.pop("ATLAS_STATIC_MODE", None)

        return report

    # ------------------------------------------------------------------
    # URL enumeration
    # ------------------------------------------------------------------

    def _enumerate_urls(self) -> List[str]:
        """Return all GET URLs to crawl, in a stable order.

        Entity URLs (languages, people, concepts, orgs, events) are taken
        directly from the entity link map so that the file paths match the
        hrefs that auto_link_content() embeds in the rendered HTML.
        Non-entity parameterized routes (paradigms, clusters, odysseys, eras)
        are enumerated from the DataLoader.

        /lineage/{language_id} is excluded: each page runs a NetworkX
        spring_layout computation that is too CPU-intensive for a batch
        crawl.  The output is a standalone Plotly visualization without the
        shared base template.  PROMPT_51 can revisit if needed.
        """
        seen: set[str] = set()
        urls: List[str] = []

        def add(url: str) -> None:
            if url not in seen:
                seen.add(url)
                urls.append(url)

        # --- Static (no parameters) ---
        for route in [
            "/",
            "/compare",
            "/insights",
            "/visualizations",
            "/odysseys",
            "/narrative",
            "/narrative/crossroads",
            "/narrative/reactions",
            "/narrative/timeline",
            "/narrative/concepts",
        ]:
            add(route)

        # --- Entity URLs from the link map ---
        # Using the link map ensures file paths match the hrefs that
        # auto_link_content() generates for each entity type:
        #   languages -> /language/{name}          (spaces)
        #   people    -> /person/{name_underscore}  (underscores)
        #   concepts  -> /concept/{name_underscore} (underscores)
        #   orgs      -> /org/{name_underscore}     (underscores)
        #   events    -> /event/{slug}              (hyphens)
        link_map = self._loader.get_entity_link_map()
        for _name, url in sorted(link_map.items()):
            # Skip any URL whose last path segment contains a literal slash
            # (e.g. /language/PL/I), which would be misread as two segments.
            segments = url.lstrip("/").split("/")
            if len(segments) >= 2 and "/" in segments[-1]:
                continue
            add(url)

        # --- Non-entity parameterized routes ---

        # Paradigms
        for name in self._loader.get_all_paradigms():
            if "/" in name:
                continue
            add(f"/paradigm/{_pct_encode(name)}")

        # Clusters
        for name in self._loader.get_all_clusters():
            if "/" in name:
                continue
            add(f"/cluster/{_pct_encode(name)}")

        # Odysseys
        for lp in self._loader.get_all_learning_paths():
            add(f"/odyssey/{_pct_encode(str(lp['id']))}")

        # Era narratives
        for era in self._loader.get_all_era_summaries():
            add(f"/narrative/era/{_pct_encode(era['slug'])}")

        return urls

    # ------------------------------------------------------------------
    # Fetch and write helpers
    # ------------------------------------------------------------------

    def _fetch(self, client: Any, url: str) -> tuple[int, str]:
        """Fetch url via TestClient; return (status_code, body_text)."""
        response = client.get(url)
        return response.status_code, response.text

    def _write(self, url: str, html: str) -> Path:
        """Write html to site/<url>/index.html and return the Path.

        Path segments are URL-decoded (spaces and special chars are preserved
        as literal filesystem characters) so that relative hrefs emitted by
        the templates -- which are not percent-encoded -- resolve correctly
        against the resulting file tree.
        """
        import urllib.parse

        # Normalise: strip query string and trailing slashes
        clean = url.split("?")[0].rstrip("/")

        if clean == "" or clean == "/":
            dest = self._out / "index.html"
        else:
            # Decode each segment individually, then build subdirectory
            parts = [urllib.parse.unquote(s) for s in clean.lstrip("/").split("/") if s]
            dest = self._out.joinpath(*parts) / "index.html"

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        return dest

    # ------------------------------------------------------------------
    # Link rewriting
    # ------------------------------------------------------------------

    # File extensions that identify direct static asset references.
    # Only paths whose last segment ends in one of these are treated as
    # file refs (and left without an appended /index.html).  All other
    # paths -- including entity names that happen to contain a dot, such
    # as "Guy_L._Steele" -- are treated as directory index pages.
    _STATIC_EXTS = frozenset([
        ".css", ".js", ".mjs", ".map",
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
        ".woff", ".woff2", ".ttf", ".eot", ".otf",
        ".json", ".txt", ".xml", ".html",
    ])

    def _rewrite_links(
        self,
        html: str,
        current_url: str,
        out_dir: Optional[Path] = None,
        written_files: Optional[set] = None,
    ) -> str:
        """Rewrite absolute internal hrefs and srcs to relative paths.

        A file at site/language/C/index.html is 2 levels deep, so the
        prefix is '../../'.  href="/language/Python" becomes
        '../../language/Python/index.html'.  Static assets keep their
        extension; page paths get /index.html appended.

        When out_dir and written_files are provided, any link whose
        resolved target is not in written_files is replaced with href="#"
        so that the static site contains no broken internal links.  This
        handles entities that 404 on the live app, excluded routes (e.g.
        /lineage/), and names containing URL-unsafe characters.

        HTML entities in href values (e.g. &amp;) are decoded before path
        processing so that concept names with ampersands resolve correctly.
        """
        import html as _html_lib
        depth = _url_depth(current_url)
        prefix = "../" * depth  # e.g. "../../" for depth 2

        def rewrite_attr(m: "re.Match[str]") -> str:
            attr = m.group(1)   # 'href' or 'src'
            quote = m.group(2)  # '"' or "'"
            raw = m.group(3)    # the path value (may contain HTML entities)

            # Skip external URLs, anchors, mailto, javascript
            if (
                raw.startswith("http")
                or raw.startswith("//")
                or raw.startswith("#")
                or raw.startswith("mailto:")
                or raw.startswith("javascript:")
            ):
                return m.group(0)

            # Skip non-rooted paths (already relative)
            if not raw.startswith("/"):
                return m.group(0)

            # HTML-decode so that &amp; -> & before path operations
            path = _html_lib.unescape(raw)
            stripped = path.lstrip("/")

            # Root href (href="/") -> relative path to index.html
            if not stripped:
                if written_files is not None and out_dir is not None:
                    target = (out_dir / "index.html").resolve()
                    if target not in written_files:
                        return f'{attr}={quote}#{quote}'
                return f'{attr}={quote}{prefix}index.html{quote}'

            # Static assets (rooted under /static/) keep their extension
            if stripped.startswith("static/"):
                return f'{attr}={quote}{prefix}{stripped}{quote}'

            # Paths whose last segment ends in a known file extension are
            # treated as direct file refs (no /index.html appended).
            last_segment = stripped.rsplit("/", 1)[-1]
            if "." in last_segment:
                ext = "." + last_segment.rsplit(".", 1)[-1].lower()
                if ext in self._STATIC_EXTS:
                    return f'{attr}={quote}{prefix}{stripped}{quote}'

            # Internal page path: append /index.html and check existence.
            rel_path = f"{stripped}/index.html"
            if written_files is not None and out_dir is not None:
                target = (out_dir / rel_path).resolve()
                if target not in written_files:
                    # Target was not written (404, excluded, or unsafe URL).
                    # Use '#' to avoid a broken link in the static export.
                    return f'{attr}={quote}#{quote}'

            return f'{attr}={quote}{prefix}{rel_path}{quote}'

        pattern = re.compile(r'(href|src)=(["\'])(/[^"\']*)\2')
        return pattern.sub(rewrite_attr, html)

    # ------------------------------------------------------------------
    # Static asset copy
    # ------------------------------------------------------------------

    def _copy_static_assets(self) -> None:
        """Mirror src/app/static/ into site/static/ recursively."""
        # Resolve src/app/static relative to this file
        this_dir = Path(__file__).parent
        src_static = this_dir.parent / "static"
        dst_static = self._out / "static"

        src_static.mkdir(parents=True, exist_ok=True)
        dst_static.mkdir(parents=True, exist_ok=True)

        if any(src_static.iterdir()):
            shutil.copytree(src_static, dst_static, dirs_exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct_encode(value: str) -> str:
    """Percent-encode a URL path segment, preserving hyphens and dots."""
    import urllib.parse
    return urllib.parse.quote(value, safe="-._~")


def _url_depth(url: str) -> int:
    """Return the number of path segments in url, excluding query string."""
    path = url.split("?")[0].rstrip("/")
    if not path or path == "/":
        return 0
    return len([s for s in path.lstrip("/").split("/") if s])


# ---------------------------------------------------------------------------
# __main__ dispatch
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    mode_html = "--html" in sys.argv

    os.environ.setdefault("USE_SQLITE", "1")
    loader = DataLoader()

    if mode_html:
        repo_root = Path(__file__).parent.parent.parent.parent
        out_dir = repo_root / "site"
        print(f"Building static HTML site into {out_dir} ...")
        crawler = SiteCrawler(loader, out_dir)
        report = crawler.crawl()
        print(f"  Written: {report.ok_count} files")
        if report.failures:
            print(f"  Failures: {report.fail_count}")
            for f in report.failures:
                print(f"    {f['url']}: {f['error']}")
        else:
            print("  No failures.")
    else:
        repo_root = Path(__file__).parent.parent.parent.parent
        out_dir = repo_root / "generated-docs"
        print(f"Building Markdown docs into {out_dir} ...")
        SiteBuilder(loader, out_dir).build_markdown()
        print("Done.")
