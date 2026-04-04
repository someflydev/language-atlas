import json
import os
import re
from pathlib import Path

def normalize(name):
    if not name:
        return ""
    # Remove parentheticals like "Smalltalk-80 (later Smalltalk)"
    name = re.sub(r'\(.*\)', '', name).strip()
    # Special cases for languages
    replacements = {
        "C#": "CSharp",
        "F#": "FSharp",
        "VB.NET": "VBNET",
        "PL/I": "PLI",
        "A-0": "A-0", # Keep dash for A-0 if it exists
        "ALGOL 60": "ALGOL_60",
        "ALGOL 68": "ALGOL_68",
        "Simula 67": "SIMULA_67",
        "Smalltalk-80": "Smalltalk",
    }
    if name in replacements:
        return replacements[name]
    
    # General normalization: replace spaces with underscores
    # We should be careful about dashes. Many files use underscores.
    # Let's try both or be consistent.
    n = name.replace(" ", "_")
    return n

def is_organization(name):
    if not name: return False
    org_keywords = [
        "Labs", "Computer", "Corp", "Inc", "Foundation", "W3C", "IBM", "Bell", 
        "Xerox", "Microsoft", "Google", "Facebook", "Meta", "Sun Microsystems", 
        "University", "ETH Zurich", "Institute", "Association", "Group", "Committee",
        "Mozilla", "JetBrains", "HashiCorp", "Oracle", "Digital Equipment", "AT&T",
        "Systems", "Software", "Research", "Project", "Consortium", "DARPA", "DoD"
    ]
    # Check if any keyword is in the name
    if any(keyword.lower() in name.lower() for keyword in org_keywords):
        return True
    # Common short org names
    if name.upper() in ["W3C", "IBM", "MIT", "CERN", "ACM", "IEEE", "GNU"]:
        return True
    return False

def extract_concept_name(text):
    if not text: return ""
    # Try to extract "Name" from "**Name**: Description"
    match = re.match(r'\*\*(.*?)\*\*[:\s]*', text)
    if match:
        name = match.group(1).strip()
    else:
        name = text.strip()
    
    # Strip trailing colon if present
    if name.endswith(":"):
        name = name[:-1].strip()
    
    # Remove common parentheticals that are actually part of the name in some contexts
    # but not others, to help deduplication (e.g., "Algebraic Data Types (ADTs)")
    # But wait, sometimes they are useful. Let's just strip trailing colons for now.
    
    return name

def audit():
    data_dir = Path("data")
    docs_dir = data_dir / "docs"
    profiles_dirs = {
        "languages": docs_dir / "language_profiles",
        "concepts": docs_dir / "concept_profiles",
        "organizations": docs_dir / "org_profiles"
    }

    # Inventory existing profiles
    existing_profiles = {
        "languages": set(),
        "concepts": set(),
        "organizations": set()
    }
    for cat, p_dir in profiles_dirs.items():
        if p_dir.exists():
            for f in p_dir.glob("*.json"):
                existing_profiles[cat].add(f.stem.lower()) # Use lower for case-insensitive match

    referenced_languages = set()
    referenced_concepts = set()
    referenced_organizations = set()
    ambiguous_references = set()

    # Helper to check if a normalized name exists in a category
    def profile_exists(name, category):
        norm = normalize(name)
        # Try exact, underscore-normalized, and lowercase
        variants = [norm, norm.replace("-", "_"), norm.replace("_", "-"), norm.lower(), norm.replace(" ", "_").lower()]
        for v in variants:
            if v.lower() in existing_profiles[category]:
                return True
        return False

    # 1. Crawl people.json
    people_path = data_dir / "people.json"
    people_data = []
    if people_path.exists():
        with open(people_path, "r") as f:
            people_data = json.load(f)
            for person in people_data:
                name = person.get("name")
                if is_organization(name):
                    referenced_organizations.add(name)
                
                for contrib in person.get("contributions", []):
                    # For contributions, we try to see if it's a language first
                    ambiguous_references.add(contrib)

    # 2. Crawl languages.json
    languages_path = data_dir / "languages.json"
    known_languages = set()
    if languages_path.exists():
        with open(languages_path, "r") as f:
            languages_data = json.load(f)
            for lang in languages_data:
                lang_name = lang.get("name")
                known_languages.add(lang_name)
                referenced_languages.add(lang_name)
                
                for inf in lang.get("influenced_by", []):
                    referenced_languages.add(inf)
                for inf in lang.get("influenced", []):
                    referenced_languages.add(inf)
                for inv in lang.get("key_innovations", []):
                    concept_name = extract_concept_name(inv)
                    referenced_concepts.add(concept_name)
                for creator in lang.get("creators", []):
                    if is_organization(creator):
                        referenced_organizations.add(creator)
                    elif creator == "Various":
                        pass
                    else:
                        pass

    # 3. Crawl existing profiles
    def scan_profile_data(data):
        found = []
        if isinstance(data, dict):
            for key in ["key_innovations", "key_aspects", "historical_context"]:
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        found.extend(val)
                    elif isinstance(val, str):
                        found.append(val)
            for v in data.values():
                found.extend(scan_profile_data(v))
        elif isinstance(data, list):
            for item in data:
                found.extend(scan_profile_data(item))
        return found

    for cat, p_dir in profiles_dirs.items():
        if p_dir.exists():
            for f_path in p_dir.glob("*.json"):
                try:
                    with open(f_path, "r") as f:
                        data = json.load(f)
                        extracted = scan_profile_data(data)
                        for item in extracted:
                            if isinstance(item, str):
                                concept_name = extract_concept_name(item)
                                ambiguous_references.add(concept_name)
                except Exception:
                    pass

    # 4. Categorize ambiguous references
    final_languages = referenced_languages.copy()
    final_concepts = referenced_concepts.copy()
    final_organizations = referenced_organizations.copy()

    for item in ambiguous_references:
        if item == "Various":
            continue
        if item in known_languages:
            final_languages.add(item)
        elif is_organization(item):
            final_organizations.add(item)
        else:
            if item not in final_languages and item not in final_organizations:
                final_concepts.add(item)

    # 5. Identify Gaps
    missing_languages = []
    missing_concepts = []
    missing_orgs = []

    for lang in sorted(final_languages):
        if not profile_exists(lang, "languages"):
            missing_languages.append(lang)

    for concept in sorted(final_concepts):
        if not profile_exists(concept, "concepts"):
            # Check if it might be a language
            if concept in known_languages:
                 if not profile_exists(concept, "languages"):
                     missing_languages.append(concept)
                 continue
            missing_concepts.append(concept)

    for org in sorted(final_organizations):
        if not profile_exists(org, "organizations"):
            missing_orgs.append(org)

    # Deduplicate and sort
    missing_languages = sorted(list(set(missing_languages)))
    missing_concepts = sorted(list(set([c for c in missing_concepts if c not in missing_languages])))
    missing_orgs = sorted(list(set(missing_orgs)))

    real_ambiguous = []

    todo = {
        "missing_language_profiles": missing_languages,
        "missing_concept_profiles": missing_concepts,
        "missing_org_profiles": missing_orgs,
        "ambiguous_references": real_ambiguous
    }


    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "dark_matter_todo.json", "w") as f:
        json.dump(todo, f, indent=2)

    print(f"Audit complete. Results written to {reports_dir / 'dark_matter_todo.json'}")
    print(f"Missing Languages: {len(missing_languages)}")
    print(f"Missing Concepts: {len(missing_concepts)}")
    print(f"Missing Organizations: {len(missing_orgs)}")

if __name__ == "__main__":
    audit()
