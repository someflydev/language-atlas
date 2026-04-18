#!/usr/bin/env python3
"""Suggest conservative dark matter alias candidates from the current report."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def ascii_text(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def canonicalize(value: str) -> str:
    value = ascii_text(value).lower().strip()
    if value.startswith("the "):
        value = value[4:].strip()
    value = value.replace("&", " and ").replace("/", "_").replace("-", "_").replace(" ", "_")
    value = re.sub(r"[^a-z0-9_+#.]", "", value)
    value = re.sub(r"_+", "_", value).strip("_")
    replacements = {
        "c#": "csharp",
        "f#": "fsharp",
        "vb.net": "vbnet",
    }
    return replacements.get(value, value)


def canonicalize_event(value: str) -> str:
    value = ascii_text(value).strip()
    value = re.sub(r"^\d{4}\s+", "", value)
    value = re.sub(r"^The\s+", "", value, flags=re.I)
    value = value.lower().replace("-", "_").replace(" ", "_")
    value = re.sub(r"[^a-z0-9_]", "", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def clean_parens(value: str) -> str:
    return re.sub(r"\s*\(([^()]*)\)\s*", "", value).strip()


def looks_like_descriptor_parens(value: str) -> bool:
    match = re.search(r"\(([^()]*)\)", value)
    if not match:
        return False
    inner = match.group(1).strip()
    if not inner:
        return False
    if re.fullmatch(r"\d{4}(?:[/-]\d{2,4})?(?:\s*(?:onward|present))?", inner, flags=re.I):
        return True
    descriptor_tokens = {
        "architect",
        "creator",
        "designer",
        "inventor",
        "leader",
        "pioneer",
        "co-designer",
        "cofounder",
        "co-founder",
        "scientist",
        "era",
        "reaction",
        "surge",
        "resurgence",
        "onward",
        "originator",
    }
    words = {token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9-]*", inner)}
    return bool(words & descriptor_tokens) or any(ch.isdigit() for ch in inner)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_known_terms(data_dir: Path) -> Dict[str, Dict[str, str]]:
    known: Dict[str, Dict[str, str]] = {
        "language": {},
        "person": {},
        "organization": {},
        "historical_event": {},
        "concept": {},
    }

    for item in load_json(data_dir / "languages.json"):
        name = item.get("name")
        if isinstance(name, str):
            known["language"][canonicalize(name)] = name

    for item in load_json(data_dir / "people.json"):
        name = item.get("name")
        if isinstance(name, str):
            known["person"][canonicalize(name)] = name

    for item in load_json(data_dir / "concepts.json"):
        name = item.get("name")
        if isinstance(name, str):
            known["concept"][canonicalize(name)] = name

    org_dir = data_dir / "docs" / "org_profiles"
    for path in org_dir.glob("*.json"):
        try:
            payload = load_json(path)
        except json.JSONDecodeError:
            continue
        title = payload.get("title")
        name = title.split(":", 1)[0].strip() if isinstance(title, str) and ":" in title else None
        if not name:
            name = path.stem.replace("_", " ")
        known["organization"][canonicalize(name)] = name

    event_dir = data_dir / "docs" / "historical_events"
    for path in event_dir.glob("*.json"):
        try:
            payload = load_json(path)
        except json.JSONDecodeError:
            payload = {}
        title = payload.get("title") if isinstance(payload, dict) else None
        name = title if isinstance(title, str) and title.strip() else path.stem.replace("_", " ")
        known["historical_event"][canonicalize_event(name)] = name

    return known


def iter_report_terms(report: Dict[str, Any]) -> Iterable[str]:
    keys = [
        "missing_language_profiles",
        "missing_entities",
        "missing_org_profiles",
        "missing_historical_events",
    ]
    for key in keys:
        values = report.get(key, [])
        if isinstance(values, list):
            for value in values:
                if isinstance(value, str):
                    yield value


def classify_candidate(term: str, known: Dict[str, Dict[str, str]]) -> Optional[Tuple[str, str]]:
    stripped = clean_parens(term)
    if stripped == term:
        return None

    generic = canonicalize(stripped)
    if generic in known["language"]:
        return "language", known["language"][generic]
    if generic in known["person"]:
        return "person", known["person"][generic]
    if generic in known["organization"]:
        return "organization", known["organization"][generic]
    if generic in known["concept"]:
        return "concept", known["concept"][generic]

    event = canonicalize_event(stripped)
    if event in known["historical_event"]:
        return "historical_event", known["historical_event"][event]

    return None


def collect_candidates(report: Dict[str, Any], known: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    seen: set[Tuple[str, str]] = set()

    for term in iter_report_terms(report):
        if not looks_like_descriptor_parens(term):
            continue
        match = classify_candidate(term, known)
        if not match:
            continue
        candidate_type, canonical_name = match
        pair = (term, canonical_name)
        if pair in seen:
            continue
        seen.add(pair)
        results.append(
            {
                "alias": term,
                "canonical": canonical_name,
                "type": candidate_type,
            }
        )

    results.sort(key=lambda item: (item["type"], item["canonical"], item["alias"]))
    return results


def render_json(candidates: List[Dict[str, str]]) -> str:
    payload = {"candidates": candidates}
    return json.dumps(payload, indent=2) + "\n"


def render_markdown(candidates: List[Dict[str, str]]) -> str:
    lines = ["# Dark Matter Alias Candidates", ""]
    current_type: Optional[str] = None
    for candidate in candidates:
        if candidate["type"] != current_type:
            current_type = candidate["type"]
            lines.extend([f"## {current_type}", ""])
        lines.append(f"- `{candidate['alias']}` -> `{candidate['canonical']}`")
    if not candidates:
        lines.append("No conservative candidates found.")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data", help="Atlas data directory")
    parser.add_argument(
        "--report",
        default="generated-reports/dark_matter_todo.json",
        help="Dark matter report path",
    )
    parser.add_argument(
        "--format",
        choices=("json", "md"),
        default="md",
        help="Output format",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    data_dir = Path(args.data_dir)
    report_path = Path(args.report)

    try:
        known = load_known_terms(data_dir)
        report = load_json(report_path)
    except FileNotFoundError as exc:
        print(f"Missing required file: {exc.filename}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}", file=sys.stderr)
        return 1

    candidates = collect_candidates(report, known)
    if args.format == "json":
        sys.stdout.write(render_json(candidates))
    else:
        sys.stdout.write(render_markdown(candidates))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
