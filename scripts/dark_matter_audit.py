import json
import os
import re
from pathlib import Path

def is_organization(name):
    if not name: return False
    # Guard: Orgs are rarely more than 5 words
    words = name.split()
    if len(words) > 5: return False

    # Specific high-value organizations to always capture
    top_orgs = {
        "Bell Labs", "Google", "Microsoft", "Apple", "IBM", "Xerox PARC", 
        "Mozilla", "JetBrains", "Facebook", "Meta", "Sun Microsystems",
        "W3C", "IETF", "DARPA", "MIT", "Stanford", "ETH Zurich", "Berkeley",
        "AT&T", "Digital Equipment Corporation", "DEC", "Netscape", "Oracle",
        "HashiCorp", "AWS", "Amazon", "Intel", "AMD", "NVIDIA", "Dartmouth College",
        "Remington Rand", "University of Cambridge", "University of Waterloo",
        "Xerox", "Bell Telephone Laboratories", "JetBrains", "Modular Inc."
    }
    name_lower = name.lower()
    if any(o.lower() == name_lower for o in top_orgs):
        return True

    # Check for specific organizational suffixes/keywords
    org_suffixes = [
        "Labs", "Corp", "Inc", "Foundation", "University", "Institute", 
        "Association", "Committee", "Consortium", "Group", "Systems",
        "Software", "Research", "Project", "Department", "Agency", "College"
    ]
    if any(name.endswith(" " + s) or name.endswith(" " + s + ".") for s in org_suffixes):
        if " and " in name_lower: return False
        return True
    
    if name.upper() in ["W3C", "IBM", "MIT", "CERN", "ACM", "IEEE", "GNU", "AT&T", "DEC"]:
        return True
    
    return False

def canonicalize(name):
    if not name:
        return ""
    # 1. Lowercase everything
    name = name.lower()
    
    # 2. Strip "the " from the beginning
    if name.startswith("the "):
        name = name[4:].strip()
    
    # 3. Strip organizational suffixes for better deduplication
    name = re.sub(r'\b(inc|corp|corporation|ltd|limited|llc|plc|foundation|labs|software)(\.?)(\b|$)', '', name).strip()
    
    # 4. Strip parentheticals
    name = re.sub(r'\(.*\)', '', name).strip()
    # 5. Unify dashes and spaces to underscores
    name = name.replace("-", "_").replace(" ", "_")
    
    # 6. Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    # 7. Strip trailing/leading underscores or colons
    name = name.strip("_:")
    
    # Special mapping (canonical form)
    replacements = {
        "c#": "csharp", "f#": "fsharp", "vb.net": "vbnet", "pl/i": "pli",
        "a_0": "a_0", "algol_60": "algol_60", "algol_68": "algol_68", "simula_67": "simula_67",
        "apple_inc": "apple", "xerox_parc": "xerox", "bell_telephone_laboratories": "bell_labs",
        "microsoft_research": "microsoft"
    }
    return replacements.get(name, name)

def extract_entities_from_text(text):
    """
    Scans a block of text (like a paragraph) for potential entities.
    Returns (found_concepts, found_orgs)
    """
    if not text or not isinstance(text, str):
        return [], []
    
    concepts = []
    orgs = []
    
    # 1. Extract bolded terms: **Concept Name**
    bold_matches = re.findall(r'\*\*(.*?)\*\*', text)
    for m in bold_matches:
        # Strip trailing colons or spaces
        clean_m = m.split(':')[0].strip()
        if clean_m and len(clean_m) <= 60 and len(clean_m.split()) <= 8:
            concepts.append(clean_m)
            
    # 2. Extract organizations: "at [Org Name]"
    at_matches = re.findall(r'at ([A-Z][a-z]+(?: [A-Z][a-z]+){0,3})', text)
    for m in at_matches:
        if is_organization(m):
            orgs.append(m)
            
    return concepts, orgs

def audit():
    data_dir = Path("data")
    docs_dir = data_dir / "docs"
    profiles_dirs = {
        "languages": docs_dir / "language_profiles",
        "concepts": docs_dir / "concept_profiles",
        "organizations": docs_dir / "org_profiles"
    }
    profiles_dirs["organizations"].mkdir(parents=True, exist_ok=True)

    existing_profiles = {
        "languages": set(), "concepts": set(), "organizations": set()
    }
    for cat, p_dir in profiles_dirs.items():
        if p_dir.exists():
            for f in p_dir.glob("*.json"):
                existing_profiles[cat].add(canonicalize(f.stem))

    referenced_languages = {}
    referenced_concepts = {}
    referenced_organizations = {}
    
    known_languages = set()
    known_people = set()

    # Pre-populate
    people_path = data_dir / "people.json"
    if people_path.exists():
        with open(people_path, "r") as f:
            people_data = json.load(f)
            for person in people_data:
                known_people.add(person.get("name").lower())

    languages_path = data_dir / "languages.json"
    if languages_path.exists():
        with open(languages_path, "r") as f:
            languages_data = json.load(f)
            for lang in languages_data:
                known_languages.add(canonicalize(lang.get("name")))

    def add_reference(name, target_map):
        if not name or name == "Various": return
        
        # User preference: Strip leading "The " for cleaner indexing
        if name.lower().startswith("the "):
            name = name[4:].strip()
            if name:
                name = name[0].upper() + name[1:]

        # Length guard on the entity name itself
        if len(name) > 60 or len(name.split()) > 8:
            return

        canon = canonicalize(name)
        if not canon: return
        
        # Check versioned languages
        version_match = re.match(r'^([a-z_]+)_(\d{2,4})$', canon)
        if version_match:
            base = version_match.group(1)
            if base in known_languages or base in existing_profiles["languages"]:
                return

        if canon not in target_map or (name[0].isupper() and not target_map[canon][0].isupper()):
            target_map[canon] = name

    # 1. Crawl people.json
    if people_path.exists():
        with open(people_path, "r") as f:
            people_data = json.load(f)
            for person in people_data:
                p_name = person.get("name")
                if is_organization(p_name): add_reference(p_name, referenced_organizations)
                for contrib in person.get("contributions", []): add_reference(contrib, referenced_concepts)

    # 2. Crawl languages.json
    if languages_path.exists():
        with open(languages_path, "r") as f:
            languages_data = json.load(f)
            for lang in languages_data:
                add_reference(lang.get("name"), referenced_languages)
                
                # Influences
                for inf in lang.get("influenced_by", []): 
                    add_reference(inf, referenced_languages)
                for inf in lang.get("influenced", []): 
                    add_reference(inf, referenced_languages)
                
                # Primary Use Cases & Innovations
                for field in ["primary_use_cases", "key_innovations"]:
                    for val in lang.get(field, []):
                        c, o = extract_entities_from_text(val)
                        for item in c: add_reference(item, referenced_concepts)
                        for item in o: add_reference(item, referenced_organizations)
                        # If it wasn't bolded, the whole string might be a concept
                        if not c:
                            add_reference(val, referenced_concepts)
                
                # Paradigms
                for paradigm in lang.get("paradigms", []):
                    # We can track these separately if we want, or just as concepts
                    # But the user asked to ensure they are in data/paradigms.json
                    add_reference(paradigm, referenced_concepts)

                for creator in lang.get("creators", []):
                    if is_organization(creator): add_reference(creator, referenced_organizations)
                    else: add_reference(creator, referenced_concepts)

    # Paradigms Check (Specific request)
    missing_paradigms = []
    paradigms_path = data_dir / "paradigms.json"
    if paradigms_path.exists() and languages_path.exists():
        with open(paradigms_path, "r") as f:
            paradigms_data = json.load(f)
            known_paradigms = {canonicalize(p["name"]) for p in paradigms_data}
        
        with open(languages_path, "r") as f:
            languages_data = json.load(f)
            for lang in languages_data:
                for p in lang.get("paradigms", []):
                    if canonicalize(p) not in known_paradigms:
                        missing_paradigms.append(p)
    
    # 3. Crawl existing profiles
    def scan_profile_data(data):
        found_concepts, found_orgs = [], []
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (str, list)):
                    texts = v if isinstance(v, list) else [v]
                    for t in texts:
                        if isinstance(t, str):
                            c, o = extract_entities_from_text(t)
                            found_concepts.extend(c)
                            found_orgs.extend(o)
                            # For list fields that aren't narrative, 
                            # the whole item might be the entity
                            if k in ["key_innovations", "key_aspects", "creators", "contributions"]:
                                if not c: # No bolding found, treat whole string as potential
                                    if is_organization(t): found_orgs.append(t)
                                    else: found_concepts.append(t)
                
                # Recurse
                if isinstance(v, (dict, list)) and k not in ["ai_assisted_discovery_missions"]:
                    c, o = scan_profile_data(v)
                    found_concepts.extend(c); found_orgs.extend(o)
                    
        elif isinstance(data, list):
            for item in data:
                c, o = scan_profile_data(item); found_concepts.extend(c); found_orgs.extend(o)
        return found_concepts, found_orgs

    for cat, p_dir in profiles_dirs.items():
        if p_dir.exists():
            for f_path in p_dir.glob("*.json"):
                try:
                    with open(f_path, "r") as f:
                        data = json.load(f)
                        c, o = scan_profile_data(data)
                        for item in c: add_reference(item, referenced_concepts)
                        for item in o: add_reference(item, referenced_organizations)
                except Exception: pass

    # 4. Filter and categorize
    missing_languages = []
    missing_concepts = []
    missing_orgs = []

    for canon, pretty in referenced_languages.items():
        if canon not in existing_profiles["languages"]: missing_languages.append(pretty)

    for canon, pretty in referenced_organizations.items():
        if canon not in existing_profiles["organizations"]: missing_orgs.append(pretty)

    org_canons = {canonicalize(o) for o in missing_orgs}
    org_canons.update(existing_profiles["organizations"])
    lang_canons = {canonicalize(l) for l in missing_languages}
    lang_canons.update(existing_profiles["languages"])
    lang_canons.update(known_languages)

    for canon, pretty in referenced_concepts.items():
        if canon in lang_canons or canon in org_canons or pretty.lower() in known_people:
            continue
        if canon not in existing_profiles["concepts"]:
            missing_concepts.append(pretty)

    todo = {
        "missing_language_profiles": sorted(list(set(missing_languages))),
        "missing_concept_profiles": sorted(list(set(missing_concepts))),
        "missing_org_profiles": sorted(list(set(missing_orgs))),
        "missing_paradigms": sorted(list(set(missing_paradigms))),
        "ambiguous_references": []
    }

    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "dark_matter_todo.json", "w") as f:
        json.dump(todo, f, indent=2)

    print(f"Audit complete. Results written to {reports_dir / 'dark_matter_todo.json'}")
    print(f"Missing Languages: {len(todo['missing_language_profiles'])}")
    print(f"Missing Concepts: {len(todo['missing_concept_profiles'])}")
    print(f"Missing Organizations: {len(todo['missing_org_profiles'])}")

if __name__ == "__main__":
    audit()
