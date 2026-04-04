#!/usr/bin/env python3
import json
import re
from pathlib import Path
import sys

def parse_markdown(content, filename):
    """
    Parses a markdown language profile into a structured dictionary.
    """
    # Extract title from H1 or fallback to filename
    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else filename.stem

    # Remove the H1 from content to avoid it being captured in the overview
    if title_match:
        content = content[:title_match.start()] + content[title_match.end():]

    # Split content into sections based on H2 headers (##)
    # The first element in 'sections' is everything BEFORE the first H2.
    # Subsequent elements alternate between header text and section body.
    sections = re.split(r'^##\s+(.*)', content, flags=re.MULTILINE)
    
    # Text before the first H2 is the initial part of the overview
    pre_h2_text = sections[0].strip()
    
    parsed_data = {
        "title": title,
        "overview": pre_h2_text,
        "historical_context": "",
        "mental_model": "",
        "key_innovations": [],
        "tradeoffs": "",
        "legacy": "",
        "ai_assisted_discovery_missions": ""
    }

    # Iterate through identified H2 sections
    for i in range(1, len(sections), 2):
        header = sections[i].strip()
        header_lower = header.lower()
        body = sections[i+1].strip() if i+1 < len(sections) else ""
        
        if "overview" in header_lower:
            # Append to pre_h2_text if it exists, otherwise set as overview
            if parsed_data["overview"]:
                parsed_data["overview"] = (parsed_data["overview"] + "\n\n" + body).strip()
            else:
                parsed_data["overview"] = body
        elif "historical context" in header_lower:
            parsed_data["historical_context"] = body
        elif "mental model" in header_lower:
            parsed_data["mental_model"] = body
        elif "key innovations" in header_lower:
            # Extract as a list of strings if formatted as a markdown list
            items = re.findall(r'^\s*[-*]\s+(.*)', body, re.MULTILINE)
            if not items:
                # Fallback to numbered list
                items = re.findall(r'^\s*\d+\.\s+(.*)', body, re.MULTILINE)
            parsed_data["key_innovations"] = [item.strip() for item in items] if items else [body]
        elif "tradeoffs" in header_lower or "criticisms" in header_lower:
            parsed_data["tradeoffs"] = body
        elif "legacy" in header_lower:
            parsed_data["legacy"] = body
        elif "ai assisted discovery missions" in header_lower or "discovery missions" in header_lower:
            parsed_data["ai_assisted_discovery_missions"] = body

    return parsed_data

def main():
    # Source and destination directories
    src_dir = Path("docs/LANGUAGE_PROFILES")
    dst_dir = Path("data/docs/language_profiles")
    dst_dir.mkdir(parents=True, exist_ok=True)

    if not src_dir.exists():
        print(f"Error: {src_dir} not found.")
        sys.exit(1)

    # Process each markdown file
    md_files = list(src_dir.glob("*.md"))
    if not md_files:
        print("No markdown files found in docs/LANGUAGE_PROFILES.")
        return

    print(f"Found {len(md_files)} profiles. Parsing...")
    
    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            data = parse_markdown(content, md_file)
            
            # Save as JSON with matching filename
            json_file = dst_dir / f"{md_file.stem}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error parsing {md_file}: {e}")
            
    print(f"Successfully processed profiles into {dst_dir}")

if __name__ == "__main__":
    main()
import re
import json
import os

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Ensure directories exist
directories = [
    'data/docs/era_summaries',
    'data/docs/concepts',
    'data/docs/crossroads',
    'data/docs/modern_reactions',
    'data/docs/paradigms',
    'data/docs/timeline'
]
for d in directories:
    ensure_dir(d)

def parse_era_summary(filepath, slug):
    with open(filepath, 'r') as f:
        content = f.read()

    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""

    overview_match = re.search(r'## Overview\n(.*?)(?=\n##|$)', content, re.DOTALL)
    overview = overview_match.group(1).strip() if overview_match else ""

    key_drivers = []
    drivers_match = re.search(r'## Key Drivers\n(.*?)(?=\n##|$)', content, re.DOTALL)
    if drivers_match:
        for m in re.finditer(r'- \*\*(.*?)\*\*(.*?)(?=\n- |\Z)', drivers_match.group(1), re.DOTALL):
            key_drivers.append({"name": m.group(1).strip(), "description": m.group(2).strip()})

    pivotal_languages = []
    langs_match = re.search(r'## Pivotal Languages\n(.*?)(?=\n##|$)', content, re.DOTALL)
    if langs_match:
        for m in re.finditer(r'\d+\.\s+\*\*(.*?)\*\*(.*?)(?=\n\d+\. |\Z)', langs_match.group(1), re.DOTALL):
            pivotal_languages.append({"name": m.group(1).strip(), "description": m.group(2).strip()})

    legacy_match = re.search(r'## Legacy & Impact\n(.*?)(?=\n---|##|$)', content, re.DOTALL)
    legacy = legacy_match.group(1).strip() if legacy_match else ""

    diagram_match = re.search(r'> \*\*Diagram Required:\*\*\s*(.*)', content)
    diagram = diagram_match.group(1).strip() if diagram_match else ""

    data = {
        "slug": slug,
        "title": title,
        "overview": overview,
        "key_drivers": key_drivers,
        "pivotal_languages": pivotal_languages,
        "legacy_impact": legacy,
        "diagram": diagram
    }
    
    outpath = f'data/docs/era_summaries/{slug}.json'
    with open(outpath, 'w') as f:
        json.dump(data, f, indent=2)

def parse_concepts(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    
    intro_match = re.search(r'^# .*?\n\n(.*?)(?=\n##)', content, re.DOTALL)
    intro = intro_match.group(1).strip() if intro_match else ""

    concepts = []
    sections = re.split(r'\n##\s+', content)
    for section in sections[1:]: # Skip the first part (title + intro)
        if section.startswith('Diagram'):
            continue
            
        header_match = re.match(r'(.*?)\n', section)
        if not header_match: continue
        name = header_match.group(1).strip()
        body = section[header_match.end():].strip()
        
        # Split body into intro and list points if present
        list_match = re.search(r'\n\* (.*)', body, re.DOTALL)
        if list_match:
            concept_intro = body[:list_match.start()].strip()
            bullets = []
            for m in re.finditer(r'\*\s+\*\*(.*?)\*\*(.*?)(?=\n\* |\Z)', list_match.group(), re.DOTALL):
                bullets.append({"name": m.group(1).strip(), "description": m.group(2).strip()})
        else:
            concept_intro = body.strip()
            bullets = []
        
        concepts.append({
            "name": name,
            "description": concept_intro,
            "bullets": bullets
        })
        
    diagram_match = re.search(r'> \*\*Diagram Required:\*\*\s*(.*)', content)
    diagram = diagram_match.group(1).strip() if diagram_match else ""
        
    data = {
        "title": title,
        "intro": intro,
        "concepts": concepts,
        "diagram": diagram
    }
    with open('data/docs/concepts/concepts_reference.json', 'w') as f:
        json.dump(data, f, indent=2)

def parse_crossroads(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
        
    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    
    intro_match = re.search(r'^# .*?\n\n(.*?)(?=\n##)', content, re.DOTALL)
    intro = intro_match.group(1).strip() if intro_match else ""

    crossroads = []
    sections = re.split(r'\n##\s+', content)
    for section in sections[1:]:
        header_match = re.match(r'(.*?)\n', section)
        if not header_match: continue
        name = header_match.group(1).strip()
        body = section[header_match.end():].strip()
        
        crossroads.append({
            "title": name,
            "explanation": body
        })

    data = {
        "title": title,
        "intro": intro,
        "crossroads": crossroads
    }
    with open('data/docs/crossroads/crossroads.json', 'w') as f:
        json.dump(data, f, indent=2)

def parse_modern_reactions(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    
    intro_match = re.search(r'^# .*?\n\n(.*?)(?=\n##)', content, re.DOTALL)
    intro = intro_match.group(1).strip() if intro_match else ""
    
    reactions = []
    sections = re.split(r'\n##\s+', content)
    for section in sections[1:]:
        header_match = re.match(r'(.*?)\n', section)
        if not header_match: continue
        name = header_match.group(1).strip()
        body = section[header_match.end():].strip()
        reactions.append({
            "theme": name,
            "explanation": body
        })

    data = {
        "title": title,
        "intro": intro,
        "reactions": reactions
    }
    with open('data/docs/modern_reactions/modern_reactions.json', 'w') as f:
        json.dump(data, f, indent=2)

def parse_paradigms(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
        
    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    
    intro_match = re.search(r'^# .*?\n\n(.*?)(?=\n##)', content, re.DOTALL)
    intro = intro_match.group(1).strip() if intro_match else ""

    paradigms = []
    sections = re.split(r'\n##\s+', content)
    for section in sections[1:]:
        header_match = re.match(r'(.*?)\n', section)
        if not header_match: continue
        name = header_match.group(1).strip()
        body = section[header_match.end():].strip()
        paradigms.append({
            "name": name,
            "explanation": body
        })

    data = {
        "title": title,
        "intro": intro,
        "paradigms": paradigms
    }
    with open('data/docs/paradigms/paradigms_reference.json', 'w') as f:
        json.dump(data, f, indent=2)
        
def parse_paradigm_matrix(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    
    intro_match = re.search(r'^# .*?\n\n(.*?)(?=\n##)', content, re.DOTALL)
    intro = intro_match.group(1).strip() if intro_match else ""

    sections = re.split(r'\n##\s+', content)
    matrix_data = []
    
    for section in sections[1:]:
        header_match = re.match(r'(.*?)\n', section)
        if not header_match: continue
        name = header_match.group(1).strip()
        body = section[header_match.end():].strip()
        
        matrix_data.append({
            "axis": name,
            "details": body
        })
        
    data = {
        "title": title,
        "intro": intro,
        "dimensions": matrix_data
    }
    with open('data/docs/paradigms/paradigm_matrix.json', 'w') as f:
        json.dump(data, f, indent=2)

def parse_timeline_old(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
        
    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    
    intro_match = re.search(r'^# .*?\n\n(.*?)(?=\n##)', content, re.DOTALL)
    intro = intro_match.group(1).strip() if intro_match else ""
    
    timeline_events = []
    sections = re.split(r'\n##\s+', content)
    for section in sections[1:]:
        header_match = re.match(r'(.*?)\n', section)
        if not header_match: continue
        name = header_match.group(1).strip()
        body = section[header_match.end():].strip()
        
        timeline_events.append({
            "era_or_period": name,
            "events": body
        })

    data = {
        "title": title,
        "intro": intro,
        "periods": timeline_events
    }
    with open('data/docs/timeline/timeline.json', 'w') as f:
        json.dump(data, f, indent=2)

def main():
    parse_era_summary('docs/ERA_SUMMARIES/MULTICORE_CRISIS.md', 'MULTICORE_CRISIS')
    parse_era_summary('docs/ERA_SUMMARIES/SYSTEMS_RENAISSANCE.md', 'SYSTEMS_RENAISSANCE')
    parse_era_summary('docs/ERA_SUMMARIES/WEB_EXPLOSION.md', 'WEB_EXPLOSION')
    parse_concepts('docs/CONCEPTS.md')
    parse_crossroads('docs/CROSSROADS.md')
    parse_modern_reactions('docs/MODERN_REACTIONS.md')
    parse_paradigms('docs/PARADIGMS.md')
    parse_paradigm_matrix('docs/PARADIGM_MATRIX.md')
    parse_timeline('docs/TIMELINE.md')

if __name__ == "__main__":
    main()
import json
import re

with open('data/docs/timeline/timeline.json', 'r') as f:
    data = json.load(f)

for period in data['periods']:
    lines = period['events'].strip().split('\n')
    events = []
    for line in lines:
        m = re.match(r'- \*\*(\d{4}[s]?(?:-\d{4})?)\*\*:\s*(.*?)(?=\s*\([a-z, ]+\)|$)(?:\s*\((.*?)\))?$', line.strip())
        if m:
            events.append({
                "year": m.group(1),
                "description": m.group(2).strip(),
                "related": [r.strip() for r in m.group(3).split(',')] if m.group(3) else []
            })
    if events:
        period['events'] = events

with open('data/docs/timeline/timeline.json', 'w') as f:
    json.dump(data, f, indent=2)

import re
import json

def parse_timeline_old(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
        
    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    
    intro_match = re.search(r'^# .*?\n\n(.*?)(?=\n##)', content, re.DOTALL)
    intro = intro_match.group(1).strip() if intro_match else ""
    
    timeline_events = []
    sections = re.split(r'\n##\s+', content)
    for section in sections[1:]:
        header_match = re.match(r'(.*?)\n', section)
        if not header_match: continue
        name = header_match.group(1).strip()
        body = section[header_match.end():].strip()
        
        events = []
        for line in body.split('\n'):
            line = line.strip()
            if not line.startswith('-'):
                continue
            line = line[1:].strip()
            # Try to match bold year
            m = re.match(r'\*\*(.*?)\*\*:\s*(.*?)(?:\s*\((.*?)\))?$', line)
            if m:
                events.append({
                    "year": m.group(1).strip(),
                    "description": m.group(2).strip(),
                    "related": [r.strip() for r in m.group(3).split(',')] if m.group(3) else []
                })
            else:
                events.append({
                    "year": "",
                    "description": line,
                    "related": []
                })
                
        timeline_events.append({
            "era_or_period": name,
            "events": events
        })

    data = {
        "title": title,
        "intro": intro,
        "periods": timeline_events
    }
    with open('data/docs/timeline/timeline.json', 'w') as f:
        json.dump(data, f, indent=2)

parse_timeline('docs/TIMELINE.md')
import re
import json

def parse_timeline(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
        
    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    
    intro_match = re.search(r'^# .*?\n\n(.*?)(?=\n##)', content, re.DOTALL)
    intro = intro_match.group(1).strip() if intro_match else ""
    
    timeline_events = []
    sections = re.split(r'\n##\s+', content)
    for section in sections[1:]:
        header_match = re.match(r'(.*?)\n', section)
        if not header_match: continue
        name = header_match.group(1).strip()
        body = section[header_match.end():].strip()
        
        events = []
        for line in body.split('\n'):
            line = line.strip()
            if not line.startswith('-'):
                continue
            line = line[1:].strip()
            # Handle standard format: - **1952**: Autocode ... (lang, lang)
            m = re.match(r'\*\*(.*?)\*\*:\s*(.*?)(?:\s*\((.*?)\))?$', line)
            if m:
                events.append({
                    "year": m.group(1).strip(),
                    "description": m.group(2).strip(),
                    "related": [r.strip() for r in m.group(3).split(',')] if m.group(3) else []
                })
            else:
                events.append({
                    "year": "",
                    "description": line,
                    "related": []
                })
                
        timeline_events.append({
            "era_or_period": name,
            "events": events
        })

    data = {
        "title": title,
        "intro": intro,
        "periods": timeline_events
    }
    with open('data/docs/timeline/timeline.json', 'w') as f:
        json.dump(data, f, indent=2)

