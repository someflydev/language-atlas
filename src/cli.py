import argparse
import sys
import os
import io
import sqlite3
from app.core.data_loader import DataLoader

def format_list(items):
    return ", ".join(items) if items else "None"

def get_io_string():
    return io.StringIO()

def list_command(loader, args):
    langs = loader.get_all_languages(filter_gen=args.generation, filter_cluster=args.cluster)
    if not langs:
        print("No languages found matching filters.")
        return
    
    output = get_io_string()
    output.write(f"{'Language':<15} | {'Year':<6} | {'Cluster':<15} | {'Generation':<12} | {'Philosophy'}\n")
    output.write("-" * 115 + "\n")
    for lang in sorted(langs, key=lambda x: x.get('year', 0)):
        philosophy = lang.get('philosophy', 'N/A')
        if len(philosophy) > 60:
            philosophy = philosophy[:57] + "..."
        output.write(f"{lang['name']:<15} | {lang.get('year', 'N/A'):<6} | {lang.get('cluster', 'N/A'):<15} | {lang.get('generation', 'N/A'):<12} | {philosophy}\n")
    print(output.getvalue())

def info_command(loader, args):
    lang = loader.get_language(args.language)
    if not lang:
        print(f"Error: Language '{args.language}' not found.")
        return
    
    output = get_io_string()
    output.write(f"--- {lang['name']} ({lang.get('year', 'N/A')}) ---\n")
    output.write(f"Creators: {format_list(lang.get('creators', []))}\n")
    output.write(f"Paradigms: {format_list(lang.get('paradigms', []))}\n")
    output.write(f"Primary Use Cases: {format_list(lang.get('primary_use_cases', []))}\n")
    output.write(f"\nPhilosophy:\n{lang.get('philosophy', 'N/A')}\n")
    output.write(f"\nMental Model:\n{lang.get('mental_model', 'N/A')}\n")
    output.write(f"\nKey Innovations: {format_list(lang.get('key_innovations', []))}\n")
    print(output.getvalue())

def influences_command(loader, args):
    influences = loader.get_influences(args.language)
    if not influences:
        print(f"Error: Language '{args.language}' not found.")
        return
    
    output = get_io_string()
    output.write(f"--- Influences for {args.language} ---\n")
    output.write(f"Influenced by: {format_list(influences['influenced_by'])}\n")
    output.write(f"Influenced:    {format_list(influences['influenced'])}\n")
    print(output.getvalue())

def paradigms_command(loader, args):
    paradigms = loader.get_all_paradigms()
    output = get_io_string()
    output.write(f"{'Paradigm':<20} | {'Description'}\n")
    output.write("-" * 60 + "\n")
    # Note: loader.get_all_paradigms() returns names if SQLite, dicts if JSON
    # This is a bit inconsistent in DataLoader, let's handle both
    for p in sorted(paradigms):
        if isinstance(p, dict):
            output.write(f"{p['name']:<20} | {p['description']}\n")
        else:
            # If SQLite, we might only have names, let's fetch desc if needed
            info = loader.get_paradigm_info(p)
            output.write(f"{info['name']:<20} | {info['description']}\n")
    print(output.getvalue())

def research_command(loader, args):
    lang = loader.get_language(args.language)
    if not lang:
        print(f"Error: Language '{args.language}' not found.")
        return
    
    output = get_io_string()
    output.write(f"--- RESEARCH BRIEF: {lang['name']} ---\n")
    output.write(f"Goal: Deep dive into {lang['name']}'s historical significance and technical nuances.\n\n")
    output.write("LLM Discovery Prompts:\n")
    output.write(f"1. Explain the architectural tradeoffs made in {lang['name']}'s {lang.get('memory_management', 'memory model')} and how it relates to its core philosophy of '{lang.get('philosophy', 'N/A')[:50]}...'.\n")
    output.write(f"2. How did {lang['name']}'s key innovation of '{lang.get('key_innovations', ['N/A'])[0]}' directly influence modern languages like {format_list(lang.get('influenced', [])[:2])}?\n")
    output.write(f"3. Construct a mental model for a {lang.get('paradigms', ['N/A'])[0]} programmer transitioning from C to {lang['name']}.\n")
    output.write(f"4. Analyze the social and economic conditions of {lang.get('year', 'N/A')} that led to the creation of {lang['name']} by {format_list(lang.get('creators', []))}.\n")
    print(output.getvalue())

def search_command(loader, args):
    results = loader.search(args.term)
    if not results:
        print(f"No results found for '{args.term}'.")
        return
    
    output = get_io_string()
    output.write(f"--- Search Results for '{args.term}' ---\n")
    for res in results:
        snippet = res.get('snippet', '')
        if snippet:
            snippet = snippet.replace('\n', ' ')[:100] + "..."
        output.write(f"[{res['category'].upper()}] {res['title']}\n")
        output.write(f"   {snippet}\n\n")
    print(output.getvalue())

def like_command(loader, args):
    if not loader.use_sqlite:
        print("Error: 'like' command requires SQLite backend. Set USE_SQLITE=1.")
        return
    
    lang = loader.get_language(args.language)
    if not lang:
        print(f"Error: Language '{args.language}' not found.")
        return

    conn = sqlite3.connect(loader.db_path)
    conn.row_factory = sqlite3.Row
    
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
    
    cursor = conn.execute(query, (lang['name'], lang['name'], lang['name'], args.limit))
    results = cursor.fetchall()
    
    output = get_io_string()
    output.write(f"--- Languages like {lang['display_name']} ---\n")
    output.write(f"{'Language':<20} | {'Score':<5} | {'Reasons'}\n")
    output.write("-" * 80 + "\n")
    for row in results:
        reasons = row['reasons']
        if len(reasons) > 50: reasons = reasons[:47] + "..."
        output.write(f"{row['display_name']:<20} | {row['total_score']:<5} | {reasons}\n")
    
    print(output.getvalue())
    conn.close()

def cross_section_command(loader, args):
    if not loader.use_sqlite:
        print("Error: 'cross-section' command requires SQLite backend. Set USE_SQLITE=1.")
        return

    conn = sqlite3.connect(loader.db_path)
    conn.row_factory = sqlite3.Row

    era_query = "SELECT slug, title FROM era_summaries WHERE slug LIKE ? OR title LIKE ?"
    era_pattern = f"%{args.era}%"
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
        print(f"[*] Matched era '{args.era}' to {era_row['title']} (Gen: {generation or 'N/A'})")
    else:
        generation = args.era.lower()

    query = """
    SELECT DISTINCT l.display_name, l.year, l.cluster, l.philosophy
    FROM languages l
    JOIN language_paradigms lp ON l.id = lp.language_id
    JOIN paradigms p ON lp.paradigm_id = p.id
    WHERE (p.name LIKE ? OR p.description LIKE ?)
    """
    params = [f"%{args.paradigm}%", f"%{args.paradigm}%"]
    
    if generation:
        query += " AND l.generation = ?"
        params.append(generation)
    
    query += " ORDER BY l.year ASC"
    
    cursor = conn.execute(query, params)
    results = cursor.fetchall()
    
    output = get_io_string()
    output.write(f"--- Cross-section: {args.paradigm} in {args.era} ---\n")
    if not results:
        output.write("No results found matching this cross-section.\n")
    else:
        output.write(f"{'Language':<20} | {'Year':<6} | {'Cluster':<15} | {'Philosophy'}\n")
        output.write("-" * 100 + "\n")
        for row in results:
            phil = row['philosophy'] or ""
            if len(phil) > 50: phil = phil[:47] + "..."
            output.write(f"{row['display_name']:<20} | {row['year']:<6} | {row['cluster']:<15} | {phil}\n")
    
    print(output.getvalue())
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Language Atlas CLI - Explore Programming Language History")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List all languages")
    list_parser.add_argument("--generation", help="Filter by generation (e.g., early, mid, modern)")
    list_parser.add_argument("--cluster", help="Filter by cluster (e.g., systems, scientific, AI)")

    # Info command
    info_parser = subparsers.add_parser("info", help="Get detailed information on a language")
    info_parser.add_argument("language", help="The name of the language")

    # Influences command
    influences_parser = subparsers.add_parser("influences", help="Explore language influences")
    influences_parser.add_argument("language", help="The name of the language")

    # Paradigms command
    subparsers.add_parser("paradigms", help="List all paradigms")

    # Research command
    research_parser = subparsers.add_parser("research", help="Generate a Research Brief for a language")
    research_parser.add_argument("language", help="The name of the language")

    # Search command
    search_parser = subparsers.add_parser("search", help="Full-text search across languages and profiles")
    search_parser.add_argument("term", help="The search term")

    # Like command
    like_parser = subparsers.add_parser("like", help="Find languages similar to X")
    like_parser.add_argument("language", help="The reference language")
    like_parser.add_argument("--limit", type=int, default=5, help="Limit number of results")

    # Cross-section command
    cs_parser = subparsers.add_parser("cross-section", help="Query cross-section of paradigms and eras")
    cs_parser.add_argument("paradigm", help="The paradigm name (e.g. Object-Oriented)")
    cs_parser.add_argument("era", help="The era name or generation (e.g. Multicore Crisis, cloud)")

    args = parser.parse_args()
    loader = DataLoader()
    
    if loader.use_sqlite:
        # Note: We print this only if it's NOT a background check
        if os.isatty(sys.stdout.fileno()):
            print(f"[*] Using SQLite backend: {loader.db_path}")

    if args.command == "list":
        list_command(loader, args)
    elif args.command == "info":
        info_command(loader, args)
    elif args.command == "influences":
        influences_command(loader, args)
    elif args.command == "paradigms":
        paradigms_command(loader, args)
    elif args.command == "research":
        research_command(loader, args)
    elif args.command == "search":
        search_command(loader, args)
    elif args.command == "like":
        like_command(loader, args)
    elif args.command == "cross-section":
        cross_section_command(loader, args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
