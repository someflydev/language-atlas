import json
import os
import re

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Ensure directories exist
directories = [
    'data/docs/concepts',
    'data/docs/paradigms',
]
for d in directories:
    ensure_dir(d)

def parse_concepts(filepath):
    if not os.path.exists(filepath): return
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

def parse_paradigms(filepath):
    if not os.path.exists(filepath): return
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
    if not os.path.exists(filepath): return
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

def main():
    parse_concepts('docs/CONCEPTS.md')
    parse_paradigms('docs/PARADIGMS.md')
    parse_paradigm_matrix('docs/PARADIGM_MATRIX.md')

if __name__ == "__main__":
    main()
