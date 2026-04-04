import json
import os
import re
from pathlib import Path

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

def canonicalize(name):
    if not name:
        return ""
    # 1. Lowercase everything
    name = name.lower()
    # 2. Strip parentheticals: "Smalltalk-80 (later Smalltalk)" -> "smalltalk-80"
    name = re.sub(r'\(.*\)', '', name).strip()
    # 3. Unify dashes and spaces to underscores
    name = name.replace("-", "_").replace(" ", "_")
    # 4. Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    # 5. Strip trailing/leading underscores or colons
    name = name.strip("_:")
    
    # Special language mapping (canonical form)
    replacements = {
        "c#": "csharp",
        "f#": "fsharp",
        "vb.net": "vbnet",
        "pl/i": "pli",
        "a_0": "a_0",
        "algol_60": "algol_60",
        "algol_68": "algol_68",
        "simula_67": "simula_67"
    }
    return replacements.get(name, name)

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

    # GUARD: If it doesn't match the bold pattern and is too long, 
    # it's likely narrative text, not a concept name.
    if not match:
        if len(name) > 60 or len(name.split()) > 8:
            return ""
    
    return name

def audit():
    data_dir = Path("data")
    docs_dir = data_dir / "docs"
    profiles_dirs = {
        "languages": docs_dir / "language_profiles",
        "concepts": docs_dir / "concept_profiles",
        "organizations": docs_dir / "org_profiles"
    }

    # Inventory existing profiles (canonical names)
    existing_profiles = {
        "languages": set(),
        "concepts": set(),
        "organizations": set()
    }
    for cat, p_dir in profiles_dirs.items():
        if p_dir.exists():
            for f in p_dir.glob("*.json"):
                existing_profiles[cat].add(canonicalize(f.stem))

    # Use maps to keep a "pretty" representative name for each canonical key
    referenced_languages = {} # canonical -> pretty
    referenced_concepts = {} # canonical -> pretty
    referenced_organizations = {} # canonical -> pretty
    
    known_languages = set()

    def add_reference(name, target_map):
        if not name or name == "Various": return
        name = extract_concept_name(name)
        if not name: return
        
        canon = canonicalize(name)
        if not canon: return
        
        # If we already have this canonical form, don't overwrite with a "worse" name
        if canon not in target_map or (name[0].isupper() and not target_map[canon][0].isupper()):
            target_map[canon] = name

    # 1. Crawl people.json
    people_path = data_dir / "people.json"
    if people_path.exists():
        with open(people_path, "r") as f:
            people_data = json.load(f)
            for person in people_data:
                name = person.get("name")
                if is_organization(name):
                    add_reference(name, referenced_organizations)
                
                for contrib in person.get("contributions", []):
                    add_reference(contrib, referenced_concepts)

    # 2. Crawl languages.json
    languages_path = data_dir / "languages.json"
    if languages_path.exists():
        with open(languages_path, "r") as f:
            languages_data = json.load(f)
            for lang in languages_data:
                lang_name = lang.get("name")
                known_languages.add(canonicalize(lang_name))
                add_reference(lang_name, referenced_languages)
                
                for inf in lang.get("influenced_by", []):
                    add_reference(inf, referenced_languages)
                for inf in lang.get("influenced", []):
                    add_reference(inf, referenced_languages)
                for inv in lang.get("key_innovations", []):
                    add_reference(inv, referenced_concepts)
                for creator in lang.get("creators", []):
                    if is_organization(creator):
                        add_reference(creator, referenced_organizations)

    # 3. Crawl existing profiles for deep-linked references
    def scan_profile_data(data):
        found = []
        if isinstance(data, dict):
            # Only scan list-based innovation/aspect fields, NOT narrative text
            for key in ["key_innovations", "key_aspects"]:
                if key in data:
                    val = data[key]
                    if isinstance(val, list): found.extend(val)
                    elif isinstance(val, str): found.append(val)
            for k, v in data.items():
                if k not in ["overview", "historical_context", "legacy", "mental_model"]:
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
                        for item in scan_profile_data(data):
                            if isinstance(item, str):
                                add_reference(extract_concept_name(item), referenced_concepts)
                except Exception: pass

    # 4. Cross-categorize and identify gaps
    missing_languages = []
    missing_concepts = []
    missing_orgs = []

    # Final Language Check
    for canon, pretty in referenced_languages.items():
        if canon not in existing_profiles["languages"]:
            missing_languages.append(pretty)

    # Final Concepts Check (removing those that are actually languages or orgs)
    for canon, pretty in referenced_concepts.items():
        if canon in known_languages:
            if canon not in existing_profiles["languages"]:
                missing_languages.append(pretty)
            continue
        
        if canon in referenced_organizations:
            if canon not in existing_profiles["organizations"]:
                missing_orgs.append(pretty)
            continue

        if canon not in existing_profiles["concepts"]:
            missing_concepts.append(pretty)

    # Final Org Check
    for canon, pretty in referenced_organizations.items():
        if canon not in existing_profiles["organizations"]:
            missing_orgs.append(pretty)

    # Deduplicate across lists and sort
    missing_languages = sorted(list(set(missing_languages)))
    missing_concepts = sorted(list(set(missing_concepts)))
    missing_orgs = sorted(list(set(missing_orgs)))
    
    # Ensure no language is listed as a concept
    final_lang_canons = {canonicalize(l) for l in missing_languages}
    missing_concepts = [c for c in missing_concepts if canonicalize(c) not in final_lang_canons]

    todo = {
        "missing_language_profiles": missing_languages,
        "missing_concept_profiles": missing_concepts,
        "missing_org_profiles": missing_orgs,
        "ambiguous_references": []
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
