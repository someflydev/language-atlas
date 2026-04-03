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
