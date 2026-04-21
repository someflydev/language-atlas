from typing import Any, Dict, List


ENTITY_TYPE_LABELS = {
    "language": "Language",
    "foundation": "Foundation",
    "artifact": "Artifact",
}


def get_entity_type_label(entity_type: str | None) -> str:
    normalized = (entity_type or "language").lower()
    return ENTITY_TYPE_LABELS.get(normalized, normalized.replace("_", " ").title())


def get_display_name(item: Dict[str, Any]) -> str:
    return str(item.get("display_name") or item.get("name") or "Unknown")


def build_upstream_lineage_sections(influences: Dict[str, Any]) -> List[Dict[str, Any]]:
    groups = influences.get("upstream_influence_groups") or []
    if groups:
        return groups

    details = influences.get("influenced_by_details") or []
    if details:
        return [
            {
                "key": "language_ancestors",
                "label": "Language Ancestors",
                "items": details,
            }
        ]

    names = influences.get("influenced_by") or []
    if names:
        return [
            {
                "key": "language_ancestors",
                "label": "Language Ancestors",
                "items": [
                    {
                        "name": name,
                        "display_name": name,
                        "entity_type": "language",
                    }
                    for name in names
                ],
            }
        ]

    return []


def build_downstream_lineage_entries(influences: Dict[str, Any]) -> List[Dict[str, Any]]:
    details = influences.get("influenced_details") or []
    if details:
        return details

    names = influences.get("influenced") or []
    return [
        {
            "name": name,
            "display_name": name,
            "entity_type": "language",
        }
        for name in names
    ]


def format_lineage_entry(item: Dict[str, Any]) -> str:
    label = get_display_name(item)
    entity_type = get_entity_type_label(item.get("entity_type"))
    influence_type = item.get("type")

    suffix_parts: List[str] = [entity_type]
    if influence_type:
        suffix_parts.append(str(influence_type))

    return f"{label} ({', '.join(suffix_parts)})"
