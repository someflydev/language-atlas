import json
import os
import re
import string
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Union

def is_organization(name: str) -> bool:
    if not name: return False
    words = name.split()
    if len(words) > 5: return False

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

    org_suffixes = [
        "Labs", "Corp", "Inc", "Foundation", "University", "Institute", 
        "Association", "Committee", "Consortium", "Group", "Systems",
        "Software", "Research", "Project", "Department", "Agency", "College", "Board"
    ]
    if any(name.endswith(" " + s) or name.endswith(" " + s + ".") for s in org_suffixes):
        if " and " in name_lower: return False
        return True
    
    if name.upper() in ["W3C", "IBM", "MIT", "CERN", "ACM", "IEEE", "GNU", "AT&T", "DEC"]:
        return True
    
    return False

def is_person(name: str) -> bool:
    if not name: return False
    words = name.split()
    if not (2 <= len(words) <= 4): return False
    
    name_particles = {"van", "von", "de", "der", "le", "da", "di", "del", "du"}
    noise = {"the", "and", "of", "for", "in", "on", "at", "with", "by", "is", "to", "a", "an", "not"}
    org_words = {"labs", "inc", "corp", "foundation", "project", "committee", "group", "systems", "agency", "department", "university", "college", "board"}
    event_words = {"conference", "war", "revolution", "crisis", "birth", "founding", "agreement", "treaty", "software", "computing", "moment", "shift", "impact"}
    
    concept_keywords = {
        "memory", "management", "system", "garbage", "collection", "type", "structure", "language", 
        "programming", "logic", "model", "control", "flow", "data", "analysis", "design", "interface",
        "machine", "architecture", "compiler", "development", "revolution", "era", "crisis", "concept",
        "paradigm", "pattern", "theory", "process", "execution", "abstract", "method", "object",
        "class", "functional", "structured", "safety", "security", "resource", "optimization", "speed",
        "stability", "compliance", "properties", "hurdles", "access", "manipulation", "interaction",
        "compatibility", "equivalence", "refinement", "discovery", "mission", "graph", "state", "search",
        "audit", "history", "evolution", "context", "snippet", "overhead", "latency", "ambiguity",
        "fragility", "pathfinding", "constraint", "abstraction", "formalism", "algorithm", "definition",
        "visualization", "engine", "narrative", "odyssey", "generator", "zenith", "maturity", "completeness",
        "pivotal", "key", "hardware", "software", "stack", "heap", "segment", "address", "pointer", "variable",
        "branching", "loop", "recursion", "closure", "acronym", "alias", "anchor", "application", "backend",
        "frontend", "browser", "byte", "channel", "circuit", "client", "server", "cluster", "code", "syntax"
    }

    for w in words:
        w_l = w.lower().strip(string.punctuation)
        if not w_l: continue
        if not w[0].isupper() and w_l not in name_particles: return False
        if w_l in noise or w_l in org_words or w_l in event_words or w_l in concept_keywords:
            return False
        
    return True

def canonicalize(name: Optional[str]) -> str:
    if not name: return ""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = name.lower()
    if name.startswith("the "): name = name[4:].strip()
    name = name.replace("cpu and memory", "cpu_memory").replace("cpu/memory", "cpu_memory")
    name = re.sub(r'\b(inc|corp|corporation|ltd|limited|llc|plc|foundation|labs|software)(\.?)(\b|$)', '', name).strip()
    name = re.sub(r'\(\d{4}(?:–|-|/)(?:\d{4}|present)\)', '', name, flags=re.I)
    name = re.sub(r'\(\d{4}\)', '', name)
    name = re.sub(r'\(proposed\)', '', name, flags=re.I)
    
    name = name.replace("-", "_").replace(" ", "_")
    name = re.sub(r'_+', '_', name)
    name = name.strip("_:")
    if name.startswith("the_"): name = name[4:]
    replacements = {
        "c#": "csharp", "f#": "fsharp", "vb.net": "vbnet", "pl/i": "pli",
        "a_0": "a_0", "algol_60": "algol_60", "algol_68": "algol_68", "simula_67": "simula_67"
    }
    return replacements.get(name, name)

LANGUAGE_PROFILE_ALIASES = {
    "bourne_shell": {
        "bourne_shell",
        "shell",
        "sh",
        "sh_bourne_shell",
        "sh_(bourne_shell)"
    },
    "python": {
        "python",
        "python_current_state",
        "python_(current_state)"
    },
    "javascript": {
        "javascript",
        "javascript_node.js_2009",
        "javascript_(node.js_2009)",
        "javascript_(node.js_-_2009)"
    }
}

def canonicalize_event(name: Optional[str]) -> str:
    if not name:
        return ""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = name.strip()
    name = re.sub(r'^\d{4}\s+', '', name)
    name = re.sub(r'\((?:\d{4}\s+)?([^()]*)\)$', r'\1', name).strip()
    name = re.sub(r'^The\s+', '', name, flags=re.I)
    name = name.lower().replace("-", "_").replace(" ", "_")
    name = re.sub(r'[^a-z0-9_]', '', name)
    name = re.sub(r'_+', '_', name).strip('_')
    event_aliases = {
        "garmisch_conference_on_software_engineering": "garmisch_conference",
        "birth_of_software_engineering": "garmisch_conference",
        "birth_of_software_engineering_garmisch_conference": "garmisch_conference",
        "macro_expansion_debugging_crisis": "macro_debugging_crisis",
        "rome_conference": "rome_conference",
        "software_crisis": "software_crisis",
    }
    return event_aliases.get(name, name)

def strip_years(name: str) -> str:
    """Utility to aggressively strip years and metadata from strings."""
    if not name: return ""
    name = re.sub(r'\s*\(\d{4}(?:–|-|/)(?:\d{4}|Present)\)', '', name, flags=re.I)
    name = re.sub(r'\s*\(\d{4}(?:/\d{4})?\)', '', name)
    name = re.sub(r'\s*\(Proposed\)', '', name, flags=re.I)
    return name.strip()

def clean_name(name: str) -> str:
    if not name: return ""
    name = name.replace('"', '').replace('`', '')
    name = re.sub(r'^\d+\.\s+', '', name)
    name = strip_years(name)
    name = name.strip(string.punctuation.replace(')', '').replace('(', '') + string.whitespace)
    if '(' in name and ')' not in name: name = name.split('(')[0].strip()
    if ')' in name and '(' not in name: name = name.split(')')[0].strip()
    return name.strip()

def split_entities(name: str) -> List[str]:
    if not name: return []
    if "PL/I" in name: name = name.replace("PL/I", "PL_I_PROTECTED")
    combos_to_protect = {"ARC/ORC", "AOT/JIT", "CPU/Memory", "CPU and Memory"}
    for combo in combos_to_protect:
        if combo in name: name = name.replace(combo, combo.replace("/", "_SLASH_").replace(" and ", "_AND_"))
    
    parts = re.split(r'\s*&\s*|\s+and\s+', name)
    if len(parts) > 1:
        last_part = parts[-1].strip()
        last_words = last_part.split()
        if len(last_words) > 1:
            suffix_keywords = ["compilation", "management", "model", "programming", "system", "architecture", "design", "logic", "separation"]
            suffix_found = ""
            for kw in suffix_keywords:
                if kw in last_part.lower():
                    idx = last_part.lower().find(kw)
                    suffix_found = last_part[idx:]; break
            if suffix_found:
                for i in range(len(parts) - 1):
                    if suffix_found.lower() not in parts[i].lower(): parts[i] = f"{parts[i].strip()} {suffix_found}"
    
    final_parts = []
    for p in parts:
        if "/" in p and "PL_I_PROTECTED" not in p and "_SLASH_" not in p:
            if re.search(r'(?<=[a-zA-Z])/(?=[a-zA-Z])', p): final_parts.extend(re.split(r'/', p))
            else: final_parts.append(p)
        else: final_parts.append(p)
    
    return [strip_years(p.replace("PL_I_PROTECTED", "PL/I").replace("_SLASH_", "/").replace("_AND_", " and ")).strip() for p in final_parts if p.strip()]

def extract_entities_from_text(text: Optional[str]) -> Tuple[List[str], List[str]]:
    if not text or not isinstance(text, str): return [], []
    concepts: List[str] = []
    orgs: List[str] = []
    bold_matches = re.findall(r'\*\*(.*?)\*\*', text)
    for m in bold_matches:
        for n in split_entities(m):
            n = clean_name(n)
            if n and len(n) <= 60 and len(n.split()) <= 10:
                if not re.match(r'^\d{4}$', n): concepts.append(n)
    at_matches = re.findall(r'at ([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+){0,3})', text)
    for m in at_matches:
        if is_organization(m): orgs.append(m)
    return concepts, orgs

def is_historical_event(name: str) -> bool:
    if not name: return False
    if is_person(name): return False
    event_keywords = ["Conference", "War", "Revolution", "Crisis", "Birth", "Founding", "Agreement", "Treaty"]
    return any(k in name for k in event_keywords)

def event_profile_canons(file_path: Path) -> Set[str]:
    canons: Set[str] = {canonicalize_event(file_path.stem)}
    try:
        with open(file_path, "r") as fh:
            data = json.load(fh)
        for key in ["slug", "title"]:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                canons.add(canonicalize_event(value))
    except Exception:
        pass
    return {canon for canon in canons if canon}

def audit() -> None:
    meta_concepts = {
        "The Pedagogical Engine", "Zenith State", "Guided Odyssey", "Influence Graph", 
        "Automated Dark Matter detection to track progress", "Automated Dark Matter detection", 
        "Recursive completeness checks", "Strict data-completeness requirements for new entries",
        "Maturity and Completeness", "Mapping the DNA of Code", "The Narrative Engine", 
        "The Odyssey Generator", "Auto-Odyssey generator", "Semantic Search", "Dark Matter Audit",
        "DAWN", "EARLY", "WEB", "CLOUD", "RENAISSANCE", "AUTONOMIC"
    }
    meta_canons: Set[str] = {canonicalize(c) for c in meta_concepts}
    data_dir = Path("data"); docs_dir = data_dir / "docs"
    profiles_dirs: Dict[str, Path] = {
        "languages": docs_dir / "language_profiles",
        "concepts": docs_dir / "concept_profiles",
        "organizations": docs_dir / "org_profiles",
        "historical_events": docs_dir / "historical_events",
        "atlas_meta": docs_dir / "atlas_meta",
        "concept_combos": docs_dir / "concept_combos",
        "people": docs_dir / "people_profiles"
    }
    for p_dir in profiles_dirs.values(): p_dir.mkdir(parents=True, exist_ok=True)
    existing_profiles: Dict[str, Set[str]] = {cat: set() for cat in profiles_dirs}
    for cat, p_dir in profiles_dirs.items():
        if p_dir.exists():
            for f in p_dir.glob("*.json"):
                if cat == "historical_events":
                    existing_profiles[cat].update(event_profile_canons(f))
                else:
                    canon = canonicalize(f.stem)
                    existing_profiles[cat].add(canon)
                    if cat == "languages":
                        for alias in LANGUAGE_PROFILE_ALIASES.get(canon, set()):
                            existing_profiles[cat].add(alias)

    referenced_languages: Dict[str, str] = {}
    referenced_entities: Dict[str, str] = {}
    referenced_organizations: Dict[str, str] = {}
    referenced_historical_events: Dict[str, str] = {}
    referenced_combos: Dict[str, str] = {}
    known_languages: Set[str] = set()
    known_people: Set[str] = set()

    people_path = data_dir / "people.json"
    if people_path.exists():
        with open(people_path, "r") as fh:
            for person in json.load(fh):
                name = person.get("name")
                if name:
                    known_people.add(name.lower())
                    referenced_entities[canonicalize(name)] = name

    languages_path = data_dir / "languages.json"
    if languages_path.exists():
        with open(languages_path, "r") as fh:
            for lang in json.load(fh): 
                name = lang.get("name")
                if name:
                    known_languages.add(canonicalize(name))

    def add_reference(name: Optional[str], target_map: Optional[Dict[str, str]] = None) -> None:
        if not name or name == "Various": return
        if re.search(r'^[A-Z]+\s+\(\d{4}-\d{4}\)$', name): return
        
        # Clean the name of years before processing combos
        name_no_year = strip_years(name)
        
        names = split_entities(name)
        if any(sep in name_no_year for sep in [" and ", " & ", " / "]) or (len(names) > 1):
            combo_clean = clean_name(name_no_year); canon_combo = canonicalize(combo_clean)
            if canon_combo and canon_combo not in meta_canons:
                if canon_combo not in existing_profiles["concept_combos"]: referenced_combos[canon_combo] = combo_clean
        for n in names:
            n = clean_name(n)
            if not n: continue
            if n.lower().startswith("the "):
                n = n[4:].strip()
                if n: n = n[0].upper() + n[1:]
            if len(n) > 60 or len(n.split()) > 10: continue
            if re.search(r'^\d{4}\s+Surge', n) or re.match(r'^\d{4}$', n): continue
            current_target = target_map
            if current_target is None:
                if is_historical_event(n): current_target = referenced_historical_events
                elif is_organization(n): current_target = referenced_organizations
                else: current_target = referenced_entities
            canon = canonicalize_event(n) if current_target is referenced_historical_events else canonicalize(n)
            if current_target is referenced_historical_events:
                canon = canonicalize_event(n)
            if not canon or canon in meta_canons: continue
            if current_target is referenced_entities and n.lower() in known_people:
                if canon in existing_profiles["people"]: return
            version_match = re.match(r'^([a-z_]+)_(\d{2,4})$', canon)
            if version_match:
                base = version_match.group(1)
                if base in known_languages or base in existing_profiles["languages"]: return
            if canon not in current_target or (n[0].isupper() and not current_target[canon][0].isupper()):
                current_target[canon] = n

    if people_path.exists():
        with open(people_path, "r") as fh:
            for p in json.load(fh):
                for c in p.get("contributions", []): add_reference(c)
    if languages_path.exists():
        with open(languages_path, "r") as fh:
            for l in json.load(fh):
                add_reference(l.get("name"), referenced_languages)
                for inf in l.get("influenced_by", []): add_reference(inf, referenced_languages)
                for inf in l.get("influenced", []): add_reference(inf, referenced_languages)
                for field in ["primary_use_cases", "key_innovations"]:
                    for val in l.get(field, []):
                        c, o = extract_entities_from_text(val)
                        for item in c: add_reference(item)
                        for item in o: add_reference(item, referenced_organizations)
                        if not c: add_reference(val)
                for paradigm in l.get("paradigms", []): add_reference(paradigm)
                for creator in l.get("creators", []):
                    if is_organization(creator): add_reference(creator, referenced_organizations)
                    else: add_reference(creator)
    
    concepts_path = data_dir / "concepts.json"
    if concepts_path.exists():
        with open(concepts_path, "r") as fh:
            for c in json.load(fh):
                add_reference(c.get("name"))
                bc, bo = extract_entities_from_text(c.get("description", ""))
                for item in bc: add_reference(item)
                for item in bo: add_reference(item, referenced_organizations)

    # Unified Era and Crossroads Audit from eras.json
    eras_file = data_dir / "eras.json"
    if eras_file.exists():
        with open(eras_file, "r") as fh:
            eras_data = json.load(fh)
            for era in eras_data:
                add_reference(era.get("name"))
                for driver in era.get("key_drivers", []): add_reference(driver.get("name"))
                for pl in era.get("pivotal_languages", []):
                    add_reference(pl.get("name", ""), referenced_languages)
                c, o = extract_entities_from_text(era.get("reactions_and_legacy", ""))
                for item in c: add_reference(item)
                for item in o: add_reference(item, referenced_organizations)
                
                # Audit internal crossroads
                for cr in era.get("crossroads", []):
                    add_reference(cr.get("title"))
                    for player in cr.get("key_players", []): add_reference(player)
                    for rl in cr.get("related_languages", []): add_reference(rl, referenced_languages)
                    c, o = extract_entities_from_text(cr.get("explanation", ""))
                    for item in c: add_reference(item)
                    for item in o: add_reference(item, referenced_organizations)

    def scan_profile_data(data: Any) -> Tuple[List[str], List[str]]:
        found_concepts: List[str] = []
        found_orgs: List[str] = []
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (str, list)):
                    texts = v if isinstance(v, list) else [v]
                    for t in texts:
                        if isinstance(t, str):
                            c, o = extract_entities_from_text(t); found_concepts.extend(c); found_orgs.extend(o)
                            if k in ["creators", "key_figures", "key_players", "pivotal_people", "key_innovations", "key_aspects", "contributions", "affiliations"]:
                                if not c:
                                    if is_organization(t): found_orgs.append(t)
                                    else: found_concepts.append(t)
                if isinstance(v, (dict, list)) and k not in ["ai_assisted_discovery_missions"]:
                    c, o = scan_profile_data(v); found_concepts.extend(c); found_orgs.extend(o)
        elif isinstance(data, list):
            for item in data:
                c, o = scan_profile_data(item); found_concepts.extend(c); found_orgs.extend(o)
        return found_concepts, found_orgs

    for cat, p_dir in profiles_dirs.items():
        if cat == "atlas_meta": continue
        if p_dir.exists():
            for f_path in p_dir.glob("*.json"):
                try:
                    with open(f_path, "r") as fh:
                        c, o = scan_profile_data(json.load(fh))
                        for item in c: add_reference(item)
                        for item in o: add_reference(item, referenced_organizations)
                except Exception: pass

    missing_paradigms: List[str] = []
    if Path("data/paradigms.json").exists():
        with open("data/paradigms.json", "r") as fh: 
            known_paradigms: Set[str] = {canonicalize(p.get("name")) for p in json.load(fh)}
        if Path("data/languages.json").exists():
            with open("data/languages.json", "r") as fh:
                for lang in json.load(fh):
                    for p in lang.get("paradigms", []):
                        if canonicalize(p) not in known_paradigms: missing_paradigms.append(p)

    missing_languages: List[str] = []
    missing_entities: List[str] = []
    missing_orgs: List[str] = []
    missing_events: List[str] = []
    missing_combos: List[str] = []
    for canon, pretty in referenced_languages.items():
        if canon not in existing_profiles["languages"]: missing_languages.append(pretty)
    for canon, pretty in referenced_organizations.items():
        if canon not in existing_profiles["organizations"]: missing_orgs.append(pretty)
    for canon, pretty in referenced_historical_events.items():
        if canon not in existing_profiles["historical_events"]: missing_events.append(pretty)
    for canon, pretty in referenced_combos.items():
        if canon not in existing_profiles["concept_combos"]: missing_combos.append(pretty)
    
    entity_canons_existing = existing_profiles["concepts"].union(existing_profiles["people"]).union(existing_profiles["atlas_meta"])
    for canon, pretty in referenced_entities.items():
        if canon in {canonicalize(l) for l in missing_languages} or canon in existing_profiles["languages"]: continue
        if canon in {canonicalize(o) for o in missing_orgs} or canon in existing_profiles["organizations"]: continue
        if canon in {canonicalize(e) for e in missing_events} or canon in existing_profiles["historical_events"]: continue
        if canon in {canonicalize(c) for c in missing_combos} or canon in existing_profiles["concept_combos"]: continue
        if canon not in entity_canons_existing: missing_entities.append(pretty)

    todo: Dict[str, Any] = {
        "missing_language_profiles": sorted(list(set(missing_languages))),
        "missing_entities": sorted(list(set(missing_entities))),
        "missing_org_profiles": sorted(list(set(missing_orgs))),
        "missing_historical_events": sorted(list(set(missing_events))),
        "missing_concept_combos": sorted(list(set(missing_combos))),
        "missing_paradigms": sorted(list(set(missing_paradigms))),
        "ambiguous_references": []
    }
    reports_dir = Path("generated-reports"); reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "dark_matter_todo.json", "w") as fh: json.dump(todo, fh, indent=2)
    print(f"Audit complete. Results written to {reports_dir / 'dark_matter_todo.json'}")
    print(f"Missing Languages: {len(todo['missing_language_profiles'])}")
    print(f"Missing Entities: {len(todo['missing_entities'])}")
    print(f"Missing Organizations: {len(todo['missing_org_profiles'])}")
    print(f"Missing Events: {len(todo['missing_historical_events'])}")
    print(f"Missing Combos: {len(todo['missing_concept_combos'])}")

if __name__ == "__main__": audit()
