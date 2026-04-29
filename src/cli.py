import typer
import sys
import os
import json
import sqlite3
import difflib
from typing import Optional, List, Dict, Any
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.columns import Columns
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text
from rich import print as rprint
from app.core.data_loader import DataLoader
from app.core.insights import InsightGenerator
from app.core.terminal_ui import (
    build_downstream_lineage_entries,
    build_upstream_lineage_sections,
    format_lineage_entry,
    get_display_name,
    get_entity_type_label,
)

app = typer.Typer(help="Language Atlas CLI - Explore Programming Language History")
console = Console(width=140, height=40)

def get_loader() -> DataLoader:
    return DataLoader()

def suggest_language(loader: DataLoader, query: str) -> Optional[str]:
    """Provides a fuzzy match suggestion for a language name."""
    if loader.use_sqlite:
        with loader._get_connection() as conn:
            names = [row['name'] for row in conn.execute("SELECT name FROM languages").fetchall()]
    else:
        names = [l['name'] for l in loader.languages]
    
    matches = difflib.get_close_matches(query, names, n=1, cutoff=0.6)
    return matches[0] if matches else None

def handle_not_found(loader: DataLoader, language: str) -> None:
    suggestion = suggest_language(loader, language)
    if suggestion:
        console.print(f"[red]Error: Language '{language}' not found.[/red] Did you mean [bold cyan]{suggestion}[/bold cyan]?")
    else:
        console.print(f"[red]Error: Language '{language}' not found.[/red]")
    raise typer.Exit(1)

def output_result(data: Any, json_out: bool) -> None:
    if json_out:
        console.print_json(data=data)
    else:
        # Standard rich output is already 'pretty'
        pass


def _build_lineage_panel(influences: Dict[str, Any]) -> Panel:
    upstream_sections = build_upstream_lineage_sections(influences)
    downstream_entries = build_downstream_lineage_entries(influences)
    blocks: List[Any] = []

    if upstream_sections:
        for section in upstream_sections:
            blocks.append(Text(section["label"], style="bold green"))
            for item in section.get("items", []):
                blocks.append(Text(f"  <- {format_lineage_entry(item)}", style="green"))
            blocks.append(Text(""))
    else:
        blocks.append(Text("No recorded upstream lineage.", style="dim"))
        blocks.append(Text(""))

    blocks.append(Text("Downstream Influences", style="bold cyan"))
    if downstream_entries:
        for item in downstream_entries:
            blocks.append(Text(f"  -> {format_lineage_entry(item)}", style="cyan"))
    else:
        blocks.append(Text("  None recorded.", style="dim"))

    if blocks and isinstance(blocks[-1], Text) and not blocks[-1].plain.strip():
        blocks.pop()

    return Panel(Group(*blocks), title="Lineage Panel", border_style="green")

@app.command()
def dashboard(language: str, json_out: bool = typer.Option(False, "--json")) -> None:
    """
    The 'Impact Dashboard': Control Room style view for a language-like entity.
    """
    loader = get_loader()
    lang = loader.get_language(language)
    
    if not lang:
        handle_not_found(loader, language)
    assert lang is not None
    
    if json_out:
        console.print_json(data=lang)
        return

    # Fetch influences
    influences = loader.get_influences(language)
    assert influences is not None
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", size=10),
        Layout(name="footer", size=3)
    )
    
    layout["main"].split_row(
        Layout(name="vital_signs", ratio=1),
        Layout(name="innovations", ratio=2),
        Layout(name="lineage", ratio=2)
    )

    # Header
    title = lang.get('display_name') or lang['name']
    layout["header"].update(Panel(f"[bold magenta]{title}[/bold magenta] ({lang.get('year', 'N/A')})", style="white on blue", border_style="bright_blue"))
    
    # Vital Signs
    vital_signs = f"[bold]Year:[/bold] {lang.get('year', 'N/A')}\n"
    vital_signs += f"[bold]Entity Type:[/bold] {lang.get('entity_type', 'language')}\n"
    vital_signs += f"[bold]Cluster:[/bold] {lang.get('cluster', 'N/A')}\n"
    vital_signs += f"[bold]Keystone:[/bold] {'[bold green]YES[/bold green]' if lang.get('is_keystone') else '[red]NO[/red]'}\n"
    vital_signs += f"[bold]Gen:[/bold] {lang.get('generation', 'N/A').upper()}"
    layout["vital_signs"].update(Panel(vital_signs, title="Vital Signs", border_style="cyan"))
    
    # Innovations
    innovations = lang.get('key_innovations', [])
    colors = ["cyan", "yellow", "green", "magenta", "bright_blue", "bright_magenta"]
    if not innovations:
        innovation_list = "[dim]No specific innovations listed.[/dim]"
    else:
        innovation_list = "\n".join([f"• [bold {colors[i % len(colors)]}]{val}[/bold {colors[i % len(colors)]}]" for i, val in enumerate(innovations)])
    layout["innovations"].update(Panel(innovation_list, title="Innovation Stats", border_style="yellow"))
    
    # Lineage
    layout["lineage"].update(_build_lineage_panel(influences))
    
    # Footer
    philosophy = lang.get('philosophy', 'N/A')
    if len(philosophy) > 120:
        philosophy = philosophy[:117] + "..."
    layout["footer"].update(Panel(f"[italic]{philosophy}[/italic]", title="Philosophy Snippet", border_style="dim"))

    console.print(layout)


@app.command("paradigm")
def paradigm_view(name: str, json_out: bool = typer.Option(False, "--json")) -> None:
    """
    Explore a paradigm ecosystem with ranked foundations and member languages.
    """
    loader = get_loader()
    ecosystem = loader.get_paradigm_ecosystem(name)
    paradigm = ecosystem.get("paradigm") or {}

    if not paradigm.get("name"):
        console.print(f"[red]Error: Paradigm '{name}' not found.[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(data=ecosystem)
        return

    stats = ecosystem.get("stats") or {}
    foundations = ecosystem.get("foundations") or []
    languages = ecosystem.get("languages") or []

    stats_table = Table.grid(expand=True)
    stats_table.add_column(style="cyan")
    stats_table.add_column(style="bold white")
    stats_table.add_row("Languages", str(stats.get("language_count", len(languages))))
    stats_table.add_row("Foundations", str(stats.get("foundation_count", len(foundations))))
    stats_table.add_row(
        "Earliest Language",
        str(stats.get("earliest_language_year") or "Unknown"),
    )
    stats_table.add_row(
        "Earliest Foundation",
        str(stats.get("earliest_foundation_year") or "Unknown"),
    )

    foundation_table = Table(box=None, show_header=True, header_style="bold green")
    foundation_table.add_column("Foundation", style="green")
    foundation_table.add_column("Why It Matters", style="white")
    foundation_table.add_column("Signals", style="cyan")
    if foundations:
        for foundation in foundations:
            signals = []
            if foundation.get("supporting_language_count"):
                signals.append(
                    f"{foundation['supporting_language_count']} supporting language(s)"
                )
            if foundation.get("example_languages"):
                signals.append(
                    "Examples: " + ", ".join(foundation["example_languages"])
                )
            if foundation.get("is_directly_tagged"):
                signals.append("Directly tagged")
            foundation_table.add_row(
                get_display_name(foundation),
                foundation.get("relevance_reason")
                or foundation.get("philosophy")
                or "No rationale recorded.",
                "; ".join(signals) or "No supporting signals recorded.",
            )
    else:
        foundation_table.add_row("None recorded", "No foundational precursors recorded.", "")

    language_table = Table(box=None, show_header=True, header_style="bold cyan")
    language_table.add_column("Language", style="cyan")
    language_table.add_column("Year", justify="right")
    language_table.add_column("Primary Paradigm", style="magenta")
    language_table.add_column("Cluster", style="green")
    if languages:
        for language in languages:
            paradigms = language.get("paradigms") or []
            language_table.add_row(
                get_display_name(language),
                str(language.get("year") or "Unknown"),
                paradigms[0] if paradigms else "Unspecified",
                language.get("cluster") or "Unspecified",
            )
    else:
        language_table.add_row("None recorded", "", "", "")

    console.print(
        Panel(
            Group(
                Text(paradigm["name"], style="bold magenta"),
                Text(paradigm.get("description") or "No description recorded.", style="white"),
                Text(""),
                stats_table,
            ),
            title="Paradigm Ecosystem",
            border_style="magenta",
        )
    )
    console.print(Panel(foundation_table, title="Foundational Precursors", border_style="green"))
    console.print(Panel(language_table, title="Languages in this paradigm", border_style="cyan"))

@app.command()
def report(subcommand: str = typer.Argument(..., help="Subcommand: summary"), json_out: bool = typer.Option(False, "--json")) -> None:
    """
    Visual Reporting: Summary and analytical reports.
    """
    if subcommand != "summary":
        console.print(f"[red]Unknown report subcommand: {subcommand}[/red]")
        raise typer.Exit(1)

    loader = get_loader()
    if loader.use_sqlite:
        with loader._get_connection() as conn:
            rows = conn.execute("SELECT year FROM languages WHERE year IS NOT NULL").fetchall()
            years = [row['year'] for row in rows]
    else:
        years = [l.get('year') for l in loader.languages if l.get('year')]
    
    if not years:
        console.print("[yellow]No year data available for summary.[/yellow]")
        return

    decades: dict[int, int] = {}
    for year in years:
        decade = (year // 10) * 10
        decades[decade] = decades.get(decade, 0) + 1
    
    if json_out:
        console.print_json(data=decades)
        return

    table = Table(title="Historical Release Density (Decade-wise)", border_style="magenta")
    table.add_column("Decade", justify="right", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right", style="bold")
    table.add_column("Density (Sparkline)", style="green")

    for decade in sorted(decades.keys()):
        count = decades[decade]
        # Simulated sparkline
        sparkline = "█" * count
        table.add_row(f"{decade}s", str(count), sparkline)

    console.print(table)

@app.command()
def leverage(
    limit: int = typer.Option(20, help="Number of results to show"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show languages ranked by pedagogical leverage score."""
    loader = get_loader()
    conn = None
    try:
        conn = loader._get_connection()
        results = InsightGenerator(conn).calculate_leverage_scores(limit=limit)
    except sqlite3.OperationalError:
        results = []
    finally:
        if conn is not None:
            conn.close()

    if json_output:
        console.print_json(data=results)
        return

    table = Table(title="Pedagogical Leverage Rankings", border_style="blue")
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Language", style="bold")
    table.add_column("Era", style="magenta")
    table.add_column("Leverage", justify="right", style="green")
    table.add_column("Descendants", justify="right")
    table.add_column("Depth", justify="right")

    for index, row in enumerate(results, start=1):
        table.add_row(
            str(index),
            row.get("display_name") or row.get("name") or "",
            str(row.get("year") or "Unknown"),
            str(row.get("leverage_score") or 0),
            str(row.get("descendant_count") or 0),
            str(row.get("max_ancestor_depth") or 0),
        )

    console.print(table)

@app.command()
def anomalies() -> None:
    """Report structural anomalies in the influence graph."""
    loader = get_loader()
    conn = None
    empty = {"deep_chains": [], "outliers": [], "era_gaps": []}
    try:
        conn = loader._get_connection()
        result = InsightGenerator(conn).detect_graph_anomalies()
    except sqlite3.OperationalError:
        result = empty
    finally:
        if conn is not None:
            conn.close()

    deep_chains = result.get("deep_chains") or []
    outliers = result.get("outliers") or []
    era_gaps = result.get("era_gaps") or []

    if not deep_chains and not outliers and not era_gaps:
        console.print("No anomalies detected.")
        return

    panels: List[Panel] = []
    deep_text = "\n".join(
        f"Depth {row['depth']}: {row['path_text']}" for row in deep_chains
    ) or "None detected"
    panels.append(Panel(deep_text, title="Deep Chains", border_style="yellow"))

    outlier_text = "\n".join(
        f"{row['name']} ({row['generation']}): z={row['z_score']}, reach={row['reachability_score']}"
        for row in outliers
    ) or "None detected"
    panels.append(Panel(outlier_text, title="Outliers", border_style="red"))

    gap_text = "\n".join(
        f"{row['from_generation']} -> {row['to_generation']}: {row['connected_count']} connection(s)"
        for row in era_gaps
    ) or "None detected"
    panels.append(Panel(gap_text, title="Era Gaps", border_style="cyan"))

    console.print(Group(*panels))

@app.command()
def info(language: str, json_out: bool = typer.Option(False, "--json"), pretty: bool = typer.Option(True, "--pretty")) -> None:
    """
    Get detailed information on a language as a syntax-highlighted report.
    """
    loader = get_loader()
    lang = loader.get_language(language)
    
    if not lang:
        handle_not_found(loader, language)
    assert lang is not None
    
    if json_out:
        console.print_json(data=lang)
        return

    md_content = f"""# {lang.get('display_name') or lang['name']} ({lang.get('year', 'N/A')})

- **Creators:** {", ".join(lang.get('creators', []))}
- **Paradigms:** {", ".join(lang.get('paradigms', []))}
- **Cluster:** {lang.get('cluster', 'N/A')}
- **Generation:** {lang.get('generation', 'N/A')}

## Philosophy
{lang.get('philosophy', 'N/A')}

## Mental Model
{lang.get('mental_model', 'N/A')}

## Key Innovations
{chr(10).join([f"- {i}" for i in lang.get('key_innovations', [])])}

## Technical Specs
- **Memory Management:** {lang.get('memory_management', 'N/A')}
- **Safety Model:** {lang.get('safety_model', 'N/A')}
- **Typing Discipline:** {lang.get('typing_discipline', 'N/A')}
"""
    console.print(Panel(Markdown(md_content), border_style="cyan"))

@app.command()
def research(language: str, json_out: bool = typer.Option(False, "--json")) -> None:
    """
    Generate a Research Brief for a language with discovery prompts.
    """
    loader = get_loader()
    lang = loader.get_language(language)
    
    if not lang:
        handle_not_found(loader, language)
    assert lang is not None

    if json_out:
        console.print_json(data=lang) # Just return language data for now
        return

    innovations = lang.get('key_innovations', ['fundamental architectural choices'])
    innovation = innovations[0] if innovations else 'core design'
    
    paradigms = lang.get('paradigms', ['multi-paradigm'])
    paradigm = paradigms[0] if paradigms else 'modern'

    md_content = f"""# RESEARCH BRIEF: {lang.get('display_name') or lang['name']}
**Goal:** Deep dive into {lang['name']}'s historical significance and technical nuances.

## LLM Discovery Prompts:
1. Explain the architectural tradeoffs made in {lang['name']}'s **{lang.get('memory_management', 'memory model')}** and how it relates to its core philosophy of *'{lang.get('philosophy', 'N/A')[:50]}...'*.
2. How did {lang['name']}'s key innovation of **'{innovation}'** directly influence modern languages?
3. Construct a mental model for a **{paradigm}** programmer transitioning from C to {lang['name']}.
4. Analyze the social and economic conditions of **{lang.get('year', 'N/A')}** that led to the creation of {lang['name']} by {", ".join(lang.get('creators', []))}.
"""
    console.print(Panel(Markdown(md_content), border_style="magenta"))

@app.command()
def list_langs(
    generation: Optional[str] = None,
    cluster: Optional[str] = None,
    entity_type: Optional[str] = typer.Option(
        "language",
        "--entity-type",
        "-e",
        help="Filter by entity type: language, foundation, or artifact",
    ),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """
    List all languages with optional filters.
    """
    loader = get_loader()
    langs = loader.get_all_languages(
        filter_gen=generation,
        filter_cluster=cluster,
        entity_type=entity_type,
    )
    
    if json_out:
        console.print_json(data=langs)
        return

    if not langs:
        console.print("[yellow]No languages found matching filters.[/yellow]")
        return
    
    table = Table(title="Languages Atlas Index", border_style="blue")
    table.add_column("Language", style="cyan")
    table.add_column("Entity Type", style="yellow")
    table.add_column("Year", justify="right")
    table.add_column("Cluster", style="green")
    table.add_column("Generation", style="magenta")
    table.add_column("Philosophy")

    for lang in sorted(langs, key=lambda x: x.get('year', 0)):
        philosophy = lang.get('philosophy', 'N/A')
        if len(philosophy) > 60:
            philosophy = philosophy[:57] + "..."
        table.add_row(
            lang['name'],
            lang.get('entity_type', 'language'),
            str(lang.get('year', 'N/A')),
            lang.get('cluster', 'N/A'),
            lang.get('generation', 'N/A'),
            philosophy
        )
    console.print(table)

@app.command()
def influences(language: str, json_out: bool = typer.Option(False, "--json")) -> None:
    """
    Explore lineage and influences for a specific language-like entity.
    """
    loader = get_loader()
    infl = loader.get_influences(language)
    
    if not infl:
        handle_not_found(loader, language)
    assert infl is not None
        
    if json_out:
        console.print_json(data=infl)
        return
    
    sections = build_upstream_lineage_sections(infl)
    downstream_entries = build_downstream_lineage_entries(infl)

    blocks: List[Any] = []
    if sections:
        for section in sections:
            table = Table(box=None, show_header=False)
            table.add_column(style="green")
            for item in section.get("items", []):
                table.add_row(f"<- {format_lineage_entry(item)}")
            blocks.append(Panel(table, title=section["label"], border_style="green"))

    downstream_table = Table(box=None, show_header=False)
    downstream_table.add_column(style="cyan")
    if downstream_entries:
        for item in downstream_entries:
            downstream_table.add_row(f"-> {format_lineage_entry(item)}")
    else:
        downstream_table.add_row("No recorded downstream influences.")
    blocks.append(Panel(downstream_table, title="Downstream Influences", border_style="cyan"))

    if not sections and not downstream_entries:
        blocks = [Panel("No lineage recorded.", border_style="dim")]

    title = loader.get_language(language)
    entity_label = get_entity_type_label(title.get("entity_type") if title else None)
    console.print(Panel(Group(*blocks), title=f"Lineage: {language} ({entity_label})", border_style="green"))

@app.command()
def search(term: str, json_out: bool = typer.Option(False, "--json")) -> None:
    """
    Full-text search across languages and profiles.
    """
    loader = get_loader()
    results = loader.search(term)
    
    if json_out:
        console.print_json(data=results)
        return

    if not results:
        console.print(f"[yellow]No results found for '{term}'.[/yellow]")
        return
    
    console.print(f"[bold]Search Results for:[/bold] [cyan]{term}[/cyan]\n")
    for res in results:
        snippet = res.get('snippet', '')
        if snippet:
            snippet = snippet.replace('\n', ' ')
            if len(snippet) > 150:
                snippet = snippet[:147] + "..."
        
        panel = Panel(
            f"{snippet}",
            title=f"[bold]{res['category'].upper()}[/bold]: {res['title']}",
            border_style="dim"
        )
        console.print(panel)

@app.command()
def like(language: str, limit: int = 5, json_out: bool = typer.Option(False, "--json")) -> None:
    """
    Find languages semantically similar to the reference language.
    """
    loader = get_loader()
    if not loader.use_sqlite:
        console.print("[red]Error: 'like' command requires SQLite backend. Set USE_SQLITE=1.[/red]")
        raise typer.Exit(1)
    
    lang = loader.get_language(language)
    if not lang:
        handle_not_found(loader, language)
    assert lang is not None

    with loader._get_connection() as conn:
        query = """
        WITH matches AS (
            SELECT l2.id, 10 as score, 'Same Cluster' as reason
            FROM languages l1, languages l2
            WHERE l1.name = ? AND l1.cluster = l2.cluster AND l1.id != l2.id
            
            UNION ALL
            
            SELECT lp2.language_id, 5, 'Shared Paradigm: ' || p.name
            FROM languages l1
            JOIN language_paradigms lp1 ON l1.id = lp1.language_id
            JOIN language_paradigms lp2 ON lp1.paradigm_id = lp2.paradigm_id
            JOIN paradigms p ON lp1.paradigm_id = p.id
            WHERE l1.name = ? AND lp2.language_id != l1.id
            
            UNION ALL
            
            SELECT i2.target_id, 8, 'Shared Ancestor'
            FROM languages l1
            JOIN influences i1 ON l1.id = i1.target_id
            JOIN influences i2 ON i1.source_id = i2.source_id
            WHERE l1.name = ? AND i2.target_id != l1.id
        )
        SELECT l.display_name, SUM(score) as total_score, GROUP_CONCAT(reason, ', ') as reasons
        FROM matches m
        JOIN languages l ON m.id = l.id
        GROUP BY l.id
        ORDER BY total_score DESC
        LIMIT ?
        """
        
        cursor = conn.execute(query, (lang['name'], lang['name'], lang['name'], limit))
        results = cursor.fetchall()
        
        if json_out:
            console.print_json(data=[dict(r) for r in results])
            return

        table = Table(title=f"Semantic Siblings: {lang.get('display_name') or lang['name']}", border_style="bright_blue")
        table.add_column("Language", style="cyan")
        table.add_column("Similarity Score", justify="right")
        table.add_column("Common Traits")
        
        for row in results:
            reasons = row['reasons']
            if len(reasons) > 60: reasons = reasons[:57] + "..."
            table.add_row(row['display_name'], str(row['total_score']), reasons)
        
        console.print(table)

@app.command()
def cross_section(paradigm: str, era: str, json_out: bool = typer.Option(False, "--json")) -> None:
    """
    Query cross-section of paradigms and eras.
    """
    loader = get_loader()
    if not loader.use_sqlite:
        console.print("[red]Error: 'cross-section' command requires SQLite backend. Set USE_SQLITE=1.[/red]")
        raise typer.Exit(1)

    with loader._get_connection() as conn:
        era_query = "SELECT slug, title FROM era_summaries WHERE slug LIKE ? OR title LIKE ?"
        era_pattern = f"%{era}%"
        era_row = conn.execute(era_query, (era_pattern, era_pattern)).fetchone()
        
        generation = None
        if era_row:
            slug = era_row['slug']
            mapping = {
                'MULTICORE_CRISIS': 'cloud',
                'SYSTEMS_RENAISSANCE': 'renaissance',
                'WEB_EXPLOSION': 'web1'
            }
            generation = mapping.get(slug)
        else:
            generation = era.lower()

        query = """
        SELECT DISTINCT l.display_name, l.year, l.cluster, l.philosophy
        FROM languages l
        JOIN language_paradigms lp ON l.id = lp.language_id
        JOIN paradigms p ON lp.paradigm_id = p.id
        WHERE (p.name LIKE ? OR p.description LIKE ?)
        """
        params = [f"%{paradigm}%", f"%{paradigm}%"]
        
        if generation:
            query += " AND l.generation = ?"
            params.append(generation)
        
        query += " ORDER BY l.year ASC"
        
        cursor = conn.execute(query, params)
        results = cursor.fetchall()
        
        if json_out:
            console.print_json(data=[dict(r) for r in results])
            return

        title = f"Cross-section: {paradigm} in {era}"
        table = Table(title=title, border_style="yellow")
        if not results:
            console.print(f"[yellow]No results found matching '{paradigm}' in '{era}'.[/yellow]")
        else:
            table.add_column("Language", style="cyan")
            table.add_column("Year", justify="right")
            table.add_column("Cluster")
            table.add_column("Philosophy")
            for row in results:
                phil = row['philosophy'] or ""
                if len(phil) > 50: phil = phil[:47] + "..."
                table.add_row(row['display_name'], str(row['year']), row['cluster'], phil)
            console.print(table)

@app.command()
def auto_odyssey(language: str) -> None:
    """
    Generate a dynamic, influence-based learning path for a given language.
    """
    loader = get_loader()
    path = loader.get_auto_odyssey(language)
    
    if not path:
        console.print(f"[yellow]Could not find influential descendants for '{language}'.[/yellow]")
        return
        
    _run_odyssey(loader, path)

@app.command()
def odyssey(path_id: Optional[str] = typer.Argument(None)) -> None:
    """
    Interactive Odyssey Mode: Guided learning paths through programming history.
    """
    loader = get_loader()
    paths = loader.get_learning_paths()
    
    if not path_id:
        table = Table(title="Available Odysseys", border_style="magenta")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Description")
        
        for p in paths:
            table.add_row(p['id'], p['title'], p['description'])
        
        console.print(table)
        console.print("\n[yellow]Run 'atlas odyssey <ID>' to start a journey.[/yellow]")
        console.print("[dim]Or use 'atlas auto-odyssey <Language>' for a dynamic legacy path.[/dim]")
        return

    path = loader.get_learning_path(path_id)
    if not path:
        console.print(f"[red]Error: Odyssey '{path_id}' not found.[/red]")
        return

    _run_odyssey(loader, path)

def _run_odyssey(loader: DataLoader, path: Dict[str, Any]) -> None:
    console.print(Panel(f"[bold magenta]{path['title']}[/bold magenta]\n\n{path['description']}", border_style="bright_magenta"))
    
    for i, step in enumerate(path['steps']):
        lang_name = step['language']
        # Use combined data to fetch the challenge from the profile
        lang = loader.get_combined_language_data(lang_name)
        
        title = f"Step {i+1}: {step['milestone']} - {lang_name}"
        
        challenge = "[dim]No specific challenge listed for this step.[/dim]"
        if lang:
            challenge = lang.get('challenge', challenge)
            
        content = f"[bold cyan]Challenge:[/bold cyan] {challenge}\n"
        
        if lang:
            content += f"\n[bold]Year:[/bold] {lang.get('year', 'N/A')}\n"
            philosophy = lang.get('philosophy', 'N/A')
            if len(philosophy) > 200: philosophy = philosophy[:197] + "..."
            content += f"[bold]Philosophy:[/bold] {philosophy}\n"
        
        console.print(Panel(content, title=title, border_style="green"))
        
        if i < len(path['steps']) - 1:
            if not typer.confirm(f"Continue to {path['steps'][i+1]['language']}?"):
                console.print("[yellow]Odyssey paused. Return any time![/yellow]")
                raise typer.Exit()
    
    console.print("\n[bold green]Congratulations! You have completed the Odyssey: " + path['title'] + "[/bold green]")

@app.command()
def tui(language: Optional[str] = typer.Argument(None, help="Optional language to select on startup")) -> None:
    """
    Launch the 'Living Atlas' TUI - Interactive historical exploration.
    """
    try:
        from tui import LivingAtlasApp
        atlas_app = LivingAtlasApp(initial_language=language)
        atlas_app.run()
    except ImportError as e:
        console.print(f"[red]Error: TUI dependencies not found. Try 'uv add textual'.[/red]")
        console.print(f"[dim]Details: {e}[/dim]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
