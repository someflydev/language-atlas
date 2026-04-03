import argparse
import sys
import os
from app.core.data_loader import DataLoader

def format_list(items):
    return ", ".join(items) if items else "None"

def list_command(loader, args):
    langs = loader.get_all_languages(filter_gen=args.generation, filter_cluster=args.cluster)
    if not langs:
        print("No languages found matching filters.")
        return
    print(f"{'Language':<15} | {'Year':<6} | {'Cluster':<15} | {'Generation':<12} | {'Philosophy'}")
    print("-" * 115)
    for lang in sorted(langs, key=lambda x: x.get('year', 0)):
        philosophy = lang.get('philosophy', 'N/A')
        if len(philosophy) > 60:
            philosophy = philosophy[:57] + "..."
        print(f"{lang['name']:<15} | {lang.get('year', 'N/A'):<6} | {lang.get('cluster', 'N/A'):<15} | {lang.get('generation', 'N/A'):<12} | {philosophy}")

def info_command(loader, args):
    lang = loader.get_language(args.language)
    if not lang:
        print(f"Error: Language '{args.language}' not found.")
        return
    
    print(f"--- {lang['name']} ({lang.get('year', 'N/A')}) ---")
    print(f"Creators: {format_list(lang.get('creators', []))}")
    print(f"Paradigms: {format_list(lang.get('paradigms', []))}")
    print(f"Primary Use Cases: {format_list(lang.get('primary_use_cases', []))}")
    print(f"\nPhilosophy:\n{lang.get('philosophy', 'N/A')}")
    print(f"\nMental Model:\n{lang.get('mental_model', 'N/A')}")
    print(f"\nKey Innovations: {format_list(lang.get('key_innovations', []))}")

def influences_command(loader, args):
    influences = loader.get_influences(args.language)
    if not influences:
        print(f"Error: Language '{args.language}' not found.")
        return
    
    print(f"--- Influences for {args.language} ---")
    print(f"Influenced by: {format_list(influences['influenced_by'])}")
    print(f"Influenced:    {format_list(influences['influenced'])}")

def paradigms_command(loader, args):
    paradigms = loader.get_all_paradigms()
    print(f"{'Paradigm':<20} | {'Description'}")
    print("-" * 60)
    for p in sorted(paradigms, key=lambda x: x['name']):
        print(f"{p['name']:<20} | {p['description']}")

def research_command(loader, args):
    lang = loader.get_language(args.language)
    if not lang:
        print(f"Error: Language '{args.language}' not found.")
        return
    
    print(f"--- RESEARCH BRIEF: {lang['name']} ---")
    print(f"Goal: Deep dive into {lang['name']}'s historical significance and technical nuances.\n")
    print("LLM Discovery Prompts:")
    print(f"1. Explain the architectural tradeoffs made in {lang['name']}'s {lang.get('memory_management', 'memory model')} and how it relates to its core philosophy of '{lang.get('philosophy', 'N/A')[:50]}...'.")
    print(f"2. How did {lang['name']}'s key innovation of '{lang.get('key_innovations', ['N/A'])[0]}' directly influence modern languages like {format_list(lang.get('influenced', [])[:2])}?")
    print(f"3. Construct a mental model for a {lang.get('paradigms', ['N/A'])[0]} programmer transitioning from C to {lang['name']}.")
    print(f"4. Analyze the social and economic conditions of {lang.get('year', 'N/A')} that led to the creation of {lang['name']} by {format_list(lang.get('creators', []))}.")

def search_command(loader, args):
    results = loader.search(args.term)
    if not results:
        print(f"No results found for '{args.term}'.")
        return
    
    print(f"--- Search Results for '{args.term}' ---")
    for res in results:
        snippet = res.get('snippet', '')
        if snippet:
            snippet = snippet.replace('\n', ' ')[:100] + "..."
        print(f"[{res['category'].upper()}] {res['title']}")
        print(f"   {snippet}\n")

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

    args = parser.parse_args()
    loader = DataLoader()
    
    if loader.use_sqlite:
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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
