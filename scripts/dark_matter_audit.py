import json
import re
import string
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


ALLOWED_CANONICAL_TYPES = {
    "language",
    "concept",
    "organization",
    "historical_event",
    "concept_combo",
    "person",
}

TYPE_TO_BUCKET = {
    "language": "languages",
    "concept": "entities",
    "organization": "organizations",
    "historical_event": "historical_events",
    "concept_combo": "concept_combos",
    "person": "entities",
}


class DarkMatterConfigError(ValueError):
    """Raised when dark matter alias metadata is invalid."""


@dataclass(frozen=True)
class CanonicalEntry:
    display_term: str
    type: str
    normalized_term: str
    profile_key: Optional[str] = None
    normalized_profile_key: Optional[str] = None

    @property
    def bucket(self) -> str:
        return TYPE_TO_BUCKET[self.type]


@dataclass(frozen=True)
class ResolvedTerm:
    display_term: str
    bucket: str
    normalized_term: str
    profile_lookup_key: str
    matched_canonical: bool = False


def is_organization(name: str) -> bool:
    if not name:
        return False
    words = name.split()
    if len(words) > 5:
        return False

    top_orgs = {
        "Bell Labs",
        "Google",
        "Microsoft",
        "Apple",
        "IBM",
        "Xerox PARC",
        "Mozilla",
        "JetBrains",
        "Facebook",
        "Meta",
        "Sun Microsystems",
        "W3C",
        "IETF",
        "DARPA",
        "MIT",
        "Stanford",
        "ETH Zurich",
        "Berkeley",
        "AT&T",
        "Digital Equipment Corporation",
        "DEC",
        "Netscape",
        "Oracle",
        "HashiCorp",
        "AWS",
        "Amazon",
        "Intel",
        "AMD",
        "NVIDIA",
        "Dartmouth College",
        "Remington Rand",
        "University of Cambridge",
        "University of Waterloo",
        "Xerox",
        "Bell Telephone Laboratories",
        "Modular Inc.",
    }
    name_lower = name.lower()
    if any(org.lower() == name_lower for org in top_orgs):
        return True

    org_suffixes = [
        "Labs",
        "Corp",
        "Inc",
        "Foundation",
        "University",
        "Institute",
        "Association",
        "Committee",
        "Consortium",
        "Group",
        "Systems",
        "Software",
        "Research",
        "Project",
        "Department",
        "Agency",
        "College",
        "Board",
    ]
    if any(name.endswith(f" {suffix}") or name.endswith(f" {suffix}.") for suffix in org_suffixes):
        if " and " in name_lower:
            return False
        return True

    if name.upper() in ["W3C", "IBM", "MIT", "CERN", "ACM", "IEEE", "GNU", "AT&T", "DEC"]:
        return True

    return False


def is_person(name: str) -> bool:
    if not name:
        return False
    words = name.split()
    if not (2 <= len(words) <= 4):
        return False

    name_particles = {"van", "von", "de", "der", "le", "da", "di", "del", "du"}
    noise = {"the", "and", "of", "for", "in", "on", "at", "with", "by", "is", "to", "a", "an", "not"}
    org_words = {
        "labs",
        "inc",
        "corp",
        "foundation",
        "project",
        "committee",
        "group",
        "systems",
        "agency",
        "department",
        "university",
        "college",
        "board",
    }
    event_words = {
        "conference",
        "war",
        "revolution",
        "crisis",
        "birth",
        "founding",
        "agreement",
        "treaty",
        "software",
        "computing",
        "moment",
        "shift",
        "impact",
    }
    concept_keywords = {
        "memory",
        "management",
        "system",
        "garbage",
        "collection",
        "type",
        "structure",
        "language",
        "programming",
        "logic",
        "model",
        "control",
        "flow",
        "data",
        "analysis",
        "design",
        "interface",
        "machine",
        "architecture",
        "compiler",
        "development",
        "revolution",
        "era",
        "crisis",
        "concept",
        "paradigm",
        "pattern",
        "theory",
        "process",
        "execution",
        "abstract",
        "method",
        "object",
        "class",
        "functional",
        "structured",
        "safety",
        "security",
        "resource",
        "optimization",
        "speed",
        "stability",
        "compliance",
        "properties",
        "hurdles",
        "access",
        "manipulation",
        "interaction",
        "compatibility",
        "equivalence",
        "refinement",
        "discovery",
        "mission",
        "graph",
        "state",
        "search",
        "audit",
        "history",
        "evolution",
        "context",
        "snippet",
        "overhead",
        "latency",
        "ambiguity",
        "fragility",
        "pathfinding",
        "constraint",
        "abstraction",
        "formalism",
        "algorithm",
        "definition",
        "visualization",
        "engine",
        "narrative",
        "odyssey",
        "generator",
        "zenith",
        "maturity",
        "completeness",
        "pivotal",
        "key",
        "hardware",
        "software",
        "stack",
        "heap",
        "segment",
        "address",
        "pointer",
        "variable",
        "branching",
        "loop",
        "recursion",
        "closure",
        "acronym",
        "alias",
        "anchor",
        "application",
        "backend",
        "frontend",
        "browser",
        "byte",
        "channel",
        "circuit",
        "client",
        "server",
        "cluster",
        "code",
        "syntax",
    }

    for word in words:
        word_lower = word.lower().strip(string.punctuation)
        if not word_lower:
            continue
        if not word[0].isupper() and word_lower not in name_particles:
            return False
        if word_lower in noise or word_lower in org_words or word_lower in event_words or word_lower in concept_keywords:
            return False

    return True


def canonicalize(name: Optional[str]) -> str:
    if not name:
        return ""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = name.lower()
    if name.startswith("the "):
        name = name[4:].strip()
    name = name.replace("cpu and memory", "cpu_memory").replace("cpu/memory", "cpu_memory")
    name = name.replace("&", " and ").replace("/", "_")
    name = re.sub(r"\b(inc|corp|corporation|ltd|limited|llc|plc|foundation|labs|software)(\.?)(\b|$)", "", name).strip()
    name = re.sub(r"\(\d{4}(?:–|-|/)(?:\d{4}|present)\)", "", name, flags=re.I)
    name = re.sub(r"\(\d{4}\)", "", name)
    name = re.sub(r"\(proposed\)", "", name, flags=re.I)

    name = name.replace("-", "_").replace(" ", "_")
    name = re.sub(r"_+", "_", name)
    name = name.strip("_:")
    if name.startswith("the_"):
        name = name[4:]
    replacements = {
        "c#": "csharp",
        "f#": "fsharp",
        "vb.net": "vbnet",
        "pl/i": "pli",
        "a_0": "a_0",
        "algol_60": "algol_60",
        "algol_68": "algol_68",
        "simula_67": "simula_67",
    }
    return replacements.get(name, name)


def canonicalize_event(name: Optional[str]) -> str:
    if not name:
        return ""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = name.strip()
    name = re.sub(r"^\d{4}\s+", "", name)
    name = re.sub(r"\((?:\d{4}\s+)?([^()]*)\)$", r"\1", name).strip()
    name = re.sub(r"^The\s+", "", name, flags=re.I)
    name = name.lower().replace("-", "_").replace(" ", "_")
    name = re.sub(r"[^a-z0-9_]", "", name)
    name = re.sub(r"_+", "_", name).strip("_")
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
    if not name:
        return ""
    name = re.sub(r"\s*\(\d{4}(?:–|-|/)(?:\d{4}|Present)\)", "", name, flags=re.I)
    name = re.sub(r"\s*\(\d{4}(?:/\d{4})?\)", "", name)
    name = re.sub(r"\s*\(Proposed\)", "", name, flags=re.I)
    return name.strip()


def clean_name(name: str) -> str:
    if not name:
        return ""
    name = name.replace('"', "").replace("`", "")
    name = re.sub(r"^\d+\.\s+", "", name)
    name = strip_years(name)
    name = name.strip(string.punctuation.replace(")", "").replace("(", "") + string.whitespace)
    if "(" in name and ")" not in name:
        name = name.split("(")[0].strip()
    if ")" in name and "(" not in name:
        name = name.split(")")[0].strip()
    return name.strip()


def split_entities(name: str) -> List[str]:
    if not name:
        return []
    if "PL/I" in name:
        name = name.replace("PL/I", "PL_I_PROTECTED")
    combos_to_protect = {"ARC/ORC", "AOT/JIT", "CPU/Memory", "CPU and Memory"}
    for combo in combos_to_protect:
        if combo in name:
            name = name.replace(combo, combo.replace("/", "_SLASH_").replace(" and ", "_AND_"))

    parts = re.split(r"\s*&\s*|\s+and\s+", name)
    if len(parts) > 1:
        last_part = parts[-1].strip()
        last_words = last_part.split()
        if len(last_words) > 1:
            suffix_keywords = [
                "compilation",
                "management",
                "model",
                "programming",
                "system",
                "architecture",
                "design",
                "logic",
                "separation",
            ]
            suffix_found = ""
            for keyword in suffix_keywords:
                if keyword in last_part.lower():
                    index = last_part.lower().find(keyword)
                    suffix_found = last_part[index:]
                    break
            if suffix_found:
                for idx in range(len(parts) - 1):
                    if suffix_found.lower() not in parts[idx].lower():
                        parts[idx] = f"{parts[idx].strip()} {suffix_found}"

    final_parts = []
    for part in parts:
        if "/" in part and "PL_I_PROTECTED" not in part and "_SLASH_" not in part:
            if re.search(r"(?<=[a-zA-Z])/(?=[a-zA-Z])", part):
                final_parts.extend(re.split(r"/", part))
            else:
                final_parts.append(part)
        else:
            final_parts.append(part)

    return [
        strip_years(part.replace("PL_I_PROTECTED", "PL/I").replace("_SLASH_", "/").replace("_AND_", " and ")).strip()
        for part in final_parts
        if part.strip()
    ]


def extract_entities_from_text(text: Optional[str]) -> Tuple[List[str], List[str]]:
    if not text or not isinstance(text, str):
        return [], []
    concepts: List[str] = []
    orgs: List[str] = []
    bold_matches = re.findall(r"\*\*(.*?)\*\*", text)
    for match in bold_matches:
        for name in split_entities(match):
            name = clean_name(name)
            if name and len(name) <= 60 and len(name.split()) <= 10:
                if not re.match(r"^\d{4}$", name):
                    concepts.append(name)
    at_matches = re.findall(r"at ([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+){0,3})", text)
    for match in at_matches:
        if is_organization(match):
            orgs.append(match)
    return concepts, orgs


def is_historical_event(name: str) -> bool:
    if not name:
        return False
    if is_person(name):
        return False
    event_keywords = ["Conference", "War", "Revolution", "Crisis", "Birth", "Founding", "Agreement", "Treaty"]
    return any(keyword in name for keyword in event_keywords)


def event_profile_canons(file_path: Path) -> Set[str]:
    canons: Set[str] = {canonicalize_event(file_path.stem)}
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        for key in ["slug", "title"]:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                canons.add(canonicalize_event(value))
    except Exception:
        pass
    return {canon for canon in canons if canon}


class DarkMatterResolver:
    def __init__(self, canonicals: Dict[str, CanonicalEntry], aliases: Dict[str, str]):
        self.canonicals = canonicals
        self.aliases = aliases

    @classmethod
    def from_data_dir(cls, data_dir: Path) -> "DarkMatterResolver":
        aliases_path = data_dir / ".dark_matter_aliases.json"
        canonicals_path = data_dir / ".dark_matter_canonicals.json"
        raw_aliases = cls._load_json_file(aliases_path, "alias")
        raw_canonicals = cls._load_json_file(canonicals_path, "canonical")
        return cls._build(raw_aliases, raw_canonicals)

    @staticmethod
    def _load_json_file(path: Path, label: str) -> Any:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DarkMatterConfigError(f"Invalid JSON in {path}: {exc}") from exc

    @classmethod
    def _build(cls, raw_aliases: Any, raw_canonicals: Any) -> "DarkMatterResolver":
        if not isinstance(raw_aliases, dict):
            raise DarkMatterConfigError("data/.dark_matter_aliases.json must contain a top-level object")
        if not isinstance(raw_canonicals, dict):
            raise DarkMatterConfigError("data/.dark_matter_canonicals.json must contain a top-level object")

        canonicals: Dict[str, CanonicalEntry] = {}
        canonical_lookup: Dict[str, str] = {}
        for display_term, payload in raw_canonicals.items():
            if not isinstance(display_term, str) or not display_term.strip():
                raise DarkMatterConfigError("Canonical terms must be non-empty strings")
            if not isinstance(payload, dict):
                raise DarkMatterConfigError(
                    f"Canonical entry for '{display_term}' must be an object with at least a type"
                )
            canonical_type = payload.get("type")
            if canonical_type not in ALLOWED_CANONICAL_TYPES:
                raise DarkMatterConfigError(
                    f"Canonical entry '{display_term}' has unsupported type '{canonical_type}'"
                )
            profile_key = payload.get("profile_key")
            if profile_key is not None and not isinstance(profile_key, str):
                raise DarkMatterConfigError(f"Canonical entry '{display_term}' has non-string profile_key")

            normalized_term = cls._normalize_for_type(display_term, canonical_type)
            if not normalized_term:
                raise DarkMatterConfigError(f"Canonical entry '{display_term}' normalizes to an empty key")
            if normalized_term in canonical_lookup:
                other_display = canonical_lookup[normalized_term]
                raise DarkMatterConfigError(
                    f"Canonical terms '{other_display}' and '{display_term}' collide after normalization"
                )

            normalized_profile_key = None
            if isinstance(profile_key, str):
                normalized_profile_key = cls._normalize_for_type(profile_key, canonical_type)
                if not normalized_profile_key:
                    raise DarkMatterConfigError(
                        f"Canonical entry '{display_term}' has a profile_key that normalizes to an empty key"
                    )

            canonical_lookup[normalized_term] = display_term
            canonicals[normalized_term] = CanonicalEntry(
                display_term=display_term,
                type=canonical_type,
                normalized_term=normalized_term,
                profile_key=profile_key,
                normalized_profile_key=normalized_profile_key,
            )

        aliases: Dict[str, str] = {}
        for alias, target in raw_aliases.items():
            if not isinstance(alias, str) or not alias.strip():
                raise DarkMatterConfigError("Alias keys must be non-empty strings")
            if not isinstance(target, str) or not target.strip():
                raise DarkMatterConfigError(f"Alias '{alias}' must point to a non-empty canonical string")

            target_entry = cls._match_canonical_target(target, canonicals)
            if target_entry is None:
                raise DarkMatterConfigError(
                    f"Alias '{alias}' points to missing canonical target '{target}'"
                )

            for normalized_alias in cls._alias_candidates(alias):
                if normalized_alias in aliases and aliases[normalized_alias] != target_entry.normalized_term:
                    existing_display = canonicals[aliases[normalized_alias]].display_term
                    raise DarkMatterConfigError(
                        f"Alias keys collide after normalization: '{alias}' conflicts with existing alias for "
                        f"'{existing_display}' on key '{normalized_alias}'"
                    )
                aliases[normalized_alias] = target_entry.normalized_term

        return cls(canonicals=canonicals, aliases=aliases)

    @staticmethod
    def _normalize_for_type(term: str, canonical_type: str) -> str:
        if canonical_type == "historical_event":
            return canonicalize_event(term)
        return canonicalize(term)

    @staticmethod
    def _alias_candidates(term: str) -> List[str]:
        cleaned = clean_name(term)
        candidates = [canonicalize(cleaned), canonicalize_event(cleaned)]
        return [candidate for idx, candidate in enumerate(candidates) if candidate and candidate not in candidates[:idx]]

    @staticmethod
    def _match_canonical_target(target: str, canonicals: Dict[str, CanonicalEntry]) -> Optional[CanonicalEntry]:
        for candidate in DarkMatterResolver._alias_candidates(target):
            entry = canonicals.get(candidate)
            if entry is not None:
                return entry
        return None

    def resolve(self, term: str, bucket_hint: Optional[str] = None) -> ResolvedTerm:
        cleaned = clean_name(term)
        for candidate in self._ordered_candidates(cleaned, bucket_hint):
            target = self.aliases.get(candidate)
            if target:
                entry = self.canonicals[target]
                return ResolvedTerm(
                    display_term=entry.display_term,
                    bucket=entry.bucket,
                    normalized_term=entry.normalized_term,
                    profile_lookup_key=entry.normalized_profile_key or entry.normalized_term,
                    matched_canonical=True,
                )

        for candidate in self._ordered_candidates(cleaned, bucket_hint):
            entry = self.canonicals.get(candidate)
            if entry:
                return ResolvedTerm(
                    display_term=entry.display_term,
                    bucket=entry.bucket,
                    normalized_term=entry.normalized_term,
                    profile_lookup_key=entry.normalized_profile_key or entry.normalized_term,
                    matched_canonical=True,
                )

        bucket = self._fallback_bucket(cleaned, bucket_hint)
        normalized_term = canonicalize_event(cleaned) if bucket == "historical_events" else canonicalize(cleaned)
        return ResolvedTerm(
            display_term=cleaned,
            bucket=bucket,
            normalized_term=normalized_term,
            profile_lookup_key=normalized_term,
            matched_canonical=False,
        )

    def _ordered_candidates(self, cleaned: str, bucket_hint: Optional[str]) -> List[str]:
        generic = canonicalize(cleaned)
        event = canonicalize_event(cleaned)
        if bucket_hint == "historical_events":
            ordered = [event, generic]
        else:
            ordered = [generic, event]
        return [candidate for idx, candidate in enumerate(ordered) if candidate and candidate not in ordered[:idx]]

    @staticmethod
    def _fallback_bucket(cleaned: str, bucket_hint: Optional[str]) -> str:
        if bucket_hint:
            return bucket_hint
        if is_historical_event(cleaned):
            return "historical_events"
        if is_organization(cleaned):
            return "organizations"
        return "entities"


def load_existing_profiles(docs_dir: Path) -> Dict[str, Set[str]]:
    profiles_dirs: Dict[str, Path] = {
        "languages": docs_dir / "language_profiles",
        "concepts": docs_dir / "concept_profiles",
        "organizations": docs_dir / "org_profiles",
        "historical_events": docs_dir / "historical_events",
        "atlas_meta": docs_dir / "atlas_meta",
        "concept_combos": docs_dir / "concept_combos",
        "people": docs_dir / "people_profiles",
    }
    for profile_dir in profiles_dirs.values():
        profile_dir.mkdir(parents=True, exist_ok=True)

    existing_profiles: Dict[str, Set[str]] = {category: set() for category in profiles_dirs}
    for category, profile_dir in profiles_dirs.items():
        for file_path in profile_dir.glob("*.json"):
            if category == "historical_events":
                existing_profiles[category].update(event_profile_canons(file_path))
                continue

            existing_profiles[category].add(canonicalize(file_path.stem))
            if category == "concept_combos":
                try:
                    payload = json.loads(file_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
                title = payload.get("title") if isinstance(payload, dict) else None
                if isinstance(title, str) and title.strip():
                    existing_profiles[category].add(canonicalize(title))
                    existing_profiles[category].add(canonicalize(title.split(":", 1)[0].strip()))
    return existing_profiles


def scan_profile_data(data: Any) -> Tuple[List[str], List[str]]:
    found_concepts: List[str] = []
    found_orgs: List[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (str, list)):
                texts = value if isinstance(value, list) else [value]
                for text in texts:
                    if isinstance(text, str):
                        concepts, orgs = extract_entities_from_text(text)
                        found_concepts.extend(concepts)
                        found_orgs.extend(orgs)
                        if key in [
                            "creators",
                            "key_figures",
                            "key_players",
                            "pivotal_people",
                            "key_innovations",
                            "key_aspects",
                            "contributions",
                            "affiliations",
                        ]:
                            if not concepts:
                                if is_organization(text):
                                    found_orgs.append(text)
                                else:
                                    found_concepts.append(text)
            if isinstance(value, (dict, list)) and key not in ["ai_assisted_discovery_missions"]:
                concepts, orgs = scan_profile_data(value)
                found_concepts.extend(concepts)
                found_orgs.extend(orgs)
    elif isinstance(data, list):
        for item in data:
            concepts, orgs = scan_profile_data(item)
            found_concepts.extend(concepts)
            found_orgs.extend(orgs)
    return found_concepts, found_orgs


def collect_dark_matter(data_dir: Path = Path("data")) -> Dict[str, Any]:
    docs_dir = data_dir / "docs"
    resolver = DarkMatterResolver.from_data_dir(data_dir)

    meta_concepts = {
        "The Pedagogical Engine",
        "Zenith State",
        "Guided Odyssey",
        "Influence Graph",
        "Automated Dark Matter detection to track progress",
        "Automated Dark Matter detection",
        "Recursive completeness checks",
        "Strict data-completeness requirements for new entries",
        "Maturity and Completeness",
        "Mapping the DNA of Code",
        "The Narrative Engine",
        "The Odyssey Generator",
        "Auto-Odyssey generator",
        "Semantic Search",
        "Dark Matter Audit",
        "DAWN",
        "EARLY",
        "WEB",
        "CLOUD",
        "RENAISSANCE",
        "AUTONOMIC",
    }
    meta_canons: Set[str] = {canonicalize(concept) for concept in meta_concepts}
    existing_profiles = load_existing_profiles(docs_dir)

    references: Dict[str, Dict[str, ResolvedTerm]] = {
        "languages": {},
        "entities": {},
        "organizations": {},
        "historical_events": {},
        "concept_combos": {},
    }
    known_languages: Set[str] = set()
    known_people_names: Set[str] = set()
    known_people_canons: Set[str] = set()

    people_path = data_dir / "people.json"
    if people_path.exists():
        for person in json.loads(people_path.read_text(encoding="utf-8")):
            name = person.get("name")
            if name:
                known_people_names.add(name.lower())
                known_people_canons.add(canonicalize(name))
                references["entities"][canonicalize(name)] = ResolvedTerm(
                    display_term=name,
                    bucket="entities",
                    normalized_term=canonicalize(name),
                    profile_lookup_key=canonicalize(name),
                    matched_canonical=False,
                )

    languages_path = data_dir / "languages.json"
    if languages_path.exists():
        for language in json.loads(languages_path.read_text(encoding="utf-8")):
            name = language.get("name")
            if name:
                known_languages.add(canonicalize(name))

    def add_reference(name: Optional[str], bucket_hint: Optional[str] = None, *, allow_combo: bool = True) -> None:
        if not isinstance(name, str) or not name or name == "Various":
            return
        if re.search(r"^[A-Z]+\s+\(\d{4}-\d{4}\)$", name):
            return

        name_without_year = strip_years(name)
        names = split_entities(name)
        if allow_combo and (any(separator in name_without_year for separator in [" and ", " & ", " / "]) or len(names) > 1):
            combo_clean = clean_name(name_without_year)
            combo_resolved = resolver.resolve(combo_clean, "concept_combos")
            if combo_resolved.normalized_term and combo_resolved.normalized_term not in meta_canons:
                bucket_map = references[combo_resolved.bucket]
                bucket_map.setdefault(combo_resolved.normalized_term, combo_resolved)

        for part in names:
            part = clean_name(part)
            if not part:
                continue
            if part.lower().startswith("the "):
                part = part[4:].strip()
                if part:
                    part = part[0].upper() + part[1:]
            if len(part) > 60 or len(part.split()) > 10:
                continue
            if re.search(r"^\d{4}\s+Surge", part) or re.match(r"^\d{4}$", part):
                continue

            resolved = resolver.resolve(part, bucket_hint)
            if not resolved.normalized_term or canonicalize(resolved.display_term) in meta_canons:
                continue

            if resolved.bucket == "entities" and part.lower() in known_people_names:
                if resolved.profile_lookup_key in existing_profiles["people"]:
                    continue
            if resolved.bucket == "entities" and resolved.normalized_term in known_people_canons:
                if resolved.profile_lookup_key in existing_profiles["people"]:
                    continue

            if resolved.bucket == "languages":
                version_match = re.match(r"^([a-z_]+)_(\d{2,4})$", resolved.profile_lookup_key)
                if version_match:
                    base = version_match.group(1)
                    if base in known_languages or base in existing_profiles["languages"]:
                        continue

            bucket_map = references[resolved.bucket]
            existing = bucket_map.get(resolved.normalized_term)
            if existing is None or (resolved.display_term and resolved.display_term[0].isupper() and not existing.display_term[0].isupper()):
                bucket_map[resolved.normalized_term] = resolved

    def add_references_from_text(text: Optional[str]) -> None:
        concepts, orgs = extract_entities_from_text(text)
        for item in concepts:
            add_reference(item)
        for item in orgs:
            add_reference(item, "organizations")

    def add_references_from_value(value: Any) -> None:
        if isinstance(value, str):
            add_references_from_text(value)
        elif isinstance(value, list):
            for item in value:
                add_references_from_value(item)
        elif isinstance(value, dict):
            for nested in value.values():
                add_references_from_value(nested)

    if people_path.exists():
        for person in json.loads(people_path.read_text(encoding="utf-8")):
            for contribution in person.get("contributions", []):
                add_reference(contribution)

    if languages_path.exists():
        for language in json.loads(languages_path.read_text(encoding="utf-8")):
            add_reference(language.get("name"), "languages")
            for field in ["influenced_by", "influenced"]:
                for value in language.get(field, []):
                    add_reference(value, "languages")
            for field in ["primary_use_cases", "key_innovations"]:
                for value in language.get(field, []):
                    concepts, orgs = extract_entities_from_text(value)
                    for item in concepts:
                        add_reference(item)
                    for item in orgs:
                        add_reference(item, "organizations")
                    if not concepts:
                        add_reference(value)
            for paradigm in language.get("paradigms", []):
                add_reference(paradigm)
            for creator in language.get("creators", []):
                if is_organization(creator):
                    add_reference(creator, "organizations")
                else:
                    add_reference(creator)

    concepts_path = data_dir / "concepts.json"
    if concepts_path.exists():
        for concept in json.loads(concepts_path.read_text(encoding="utf-8")):
            add_reference(concept.get("name"))
            add_references_from_text(concept.get("description", ""))
            for responsible in concept.get("responsible", []):
                if is_organization(responsible):
                    add_reference(responsible, "organizations")
                else:
                    add_reference(responsible)

    eras_file = data_dir / "eras.json"
    if eras_file.exists():
        for era in json.loads(eras_file.read_text(encoding="utf-8")):
            add_reference(era.get("name"))
            add_references_from_text(era.get("description", ""))
            add_references_from_text(era.get("catalyst", ""))
            for innovation in era.get("key_innovations", []):
                add_reference(innovation)
            for event in era.get("timeline_events", []):
                add_references_from_text(event.get("description", ""))
            for driver in era.get("key_drivers", []):
                add_reference(driver.get("name"))
            for pivotal_language in era.get("pivotal_languages", []):
                add_reference(pivotal_language.get("name", ""), "languages")
            add_references_from_text(era.get("reactions_and_legacy", ""))
            for reaction in era.get("modern_reactions", []):
                add_references_from_value(reaction)

            for crossroad in era.get("crossroads", []):
                add_reference(crossroad.get("title"))
                for player in crossroad.get("key_players", []):
                    add_reference(player)
                for related_language in crossroad.get("related_languages", []):
                    add_reference(related_language, "languages")
                add_references_from_text(crossroad.get("explanation", ""))

    paradigms_path = data_dir / "paradigms.json"
    if paradigms_path.exists():
        paradigms = json.loads(paradigms_path.read_text(encoding="utf-8"))
        for paradigm in paradigms:
            add_reference(paradigm.get("name"))
            add_references_from_text(paradigm.get("description", ""))
            add_references_from_text(paradigm.get("motivation", ""))
            for language_name in paradigm.get("languages", []):
                add_reference(language_name, "languages")
            for connected in paradigm.get("connected_paradigms", []):
                add_reference(connected)
            add_references_from_value(paradigm.get("key_features", {}))

    learning_paths_path = data_dir / "learning_paths.json"
    if learning_paths_path.exists():
        for learning_path in json.loads(learning_paths_path.read_text(encoding="utf-8")):
            add_references_from_text(learning_path.get("title", ""))
            add_references_from_text(learning_path.get("description", ""))
            for step in learning_path.get("steps", []):
                add_reference(step.get("language"), "languages")
                add_references_from_text(step.get("milestone", ""))
                add_references_from_text(step.get("rationale", ""))
                add_references_from_text(step.get("challenge", ""))

    profile_dirs = {
        "languages": docs_dir / "language_profiles",
        "concepts": docs_dir / "concept_profiles",
        "organizations": docs_dir / "org_profiles",
        "historical_events": docs_dir / "historical_events",
        "people": docs_dir / "people_profiles",
        "era_summaries": docs_dir / "era_summaries",
    }
    for category, profile_dir in profile_dirs.items():
        if not profile_dir.exists():
            continue
        for file_path in profile_dir.glob("*.json"):
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            concepts, orgs = scan_profile_data(payload)
            for item in concepts:
                add_reference(item)
            for item in orgs:
                add_reference(item, "organizations")

    missing_paradigms: List[str] = []
    if paradigms_path.exists():
        known_paradigms = {
            canonicalize(paradigm.get("name"))
            for paradigm in paradigms
        }
        if languages_path.exists():
            for language in json.loads(languages_path.read_text(encoding="utf-8")):
                for paradigm in language.get("paradigms", []):
                    if canonicalize(paradigm) not in known_paradigms:
                        missing_paradigms.append(paradigm)

    influences_path = data_dir / "influences.json"
    if influences_path.exists():
        for influence in json.loads(influences_path.read_text(encoding="utf-8")):
            # This file is currently redundant with language influence edges, but
            # scanning it is harmless and preserves coverage if the datasets drift.
            add_reference(influence.get("from") or influence.get("source"), "languages")
            add_reference(influence.get("to") or influence.get("target"), "languages")

    missing_languages = [
        ref.display_term
        for ref in references["languages"].values()
        if ref.profile_lookup_key not in existing_profiles["languages"]
    ]
    missing_orgs = [
        ref.display_term
        for ref in references["organizations"].values()
        if ref.profile_lookup_key not in existing_profiles["organizations"]
    ]
    missing_events = [
        ref.display_term
        for ref in references["historical_events"].values()
        if ref.profile_lookup_key not in existing_profiles["historical_events"]
    ]
    missing_combos = [
        ref.display_term
        for ref in references["concept_combos"].values()
        if ref.profile_lookup_key not in existing_profiles["concept_combos"]
    ]

    missing_language_canons = {canonicalize(name) for name in missing_languages}
    missing_org_canons = {canonicalize(name) for name in missing_orgs}
    missing_event_canons = {canonicalize_event(name) for name in missing_events}
    missing_combo_canons = {canonicalize(name) for name in missing_combos}
    entity_canons_existing = existing_profiles["concepts"].union(existing_profiles["people"]).union(existing_profiles["atlas_meta"])

    missing_entities: List[str] = []
    for ref in references["entities"].values():
        if ref.normalized_term in missing_language_canons or ref.profile_lookup_key in existing_profiles["languages"]:
            continue
        if ref.normalized_term in missing_org_canons or ref.profile_lookup_key in existing_profiles["organizations"]:
            continue
        if ref.normalized_term in missing_event_canons or ref.profile_lookup_key in existing_profiles["historical_events"]:
            continue
        if ref.normalized_term in missing_combo_canons or ref.profile_lookup_key in existing_profiles["concept_combos"]:
            continue
        if ref.profile_lookup_key not in entity_canons_existing:
            missing_entities.append(ref.display_term)

    return {
        "missing_language_profiles": sorted(set(missing_languages)),
        "missing_entities": sorted(set(missing_entities)),
        "missing_org_profiles": sorted(set(missing_orgs)),
        "missing_historical_events": sorted(set(missing_events)),
        "missing_concept_combos": sorted(set(missing_combos)),
        "missing_paradigms": sorted(set(missing_paradigms)),
        "ambiguous_references": [],
    }


def audit(data_dir: Path = Path("data"), reports_dir: Path = Path("generated-reports")) -> None:
    todo = collect_dark_matter(data_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "dark_matter_todo.json"
    report_path.write_text(json.dumps(todo, indent=2) + "\n", encoding="utf-8")
    print(f"Audit complete. Results written to {report_path}")
    print(f"Missing Languages: {len(todo['missing_language_profiles'])}")
    print(f"Missing Entities: {len(todo['missing_entities'])}")
    print(f"Missing Organizations: {len(todo['missing_org_profiles'])}")
    print(f"Missing Events: {len(todo['missing_historical_events'])}")
    print(f"Missing Combos: {len(todo['missing_concept_combos'])}")


if __name__ == "__main__":
    audit()
