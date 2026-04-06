import os
import markdown
import sqlite3
import polars as pl
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from core.data_loader import DataLoader
import uvicorn

# Ensure SQLite mode is enabled for DataLoader
os.environ['USE_SQLITE'] = '1'

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Establish a read-only SQLite connection on startup
    # This pattern is shared across the app's state for consistency
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'language_atlas.sqlite'))
    if not os.path.exists(db_path):
        print(f"CRITICAL: Database not found at {db_path}")
    
    # We use a global data_loader which handles its own connections for now, 
    # but we could also attach a pool or a single connection to app.state.
    # For a high-concurrency app we'd use a pool, but for this project 
    # DataLoader's per-call connection is safe and easy for read-only.
    yield

app = FastAPI(title="Language Atlas", lifespan=lifespan)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

import re

# Initialize data loader
data_loader = DataLoader()

# Global entity link map for auto-linking
_entity_link_map = None

def get_link_map():
    global _entity_link_map
    if _entity_link_map is None:
        _entity_link_map = data_loader.get_entity_link_map()
    return _entity_link_map

def auto_link_content(html: str) -> str:
    """Automatically wraps known entity names with HTML links, avoiding existing tags."""
    link_map = get_link_map()
    if not link_map:
        return html
    
    # Names to look for, sorted by length descending
    sorted_names = sorted(link_map.keys(), key=len, reverse=True)
    
    # Regex to match names NOT inside <a> or <code> or <pre> tags
    # This is a bit complex for pure regex, so we'll use a simpler heuristic:
    # Match the pattern ONLY if it's not preceded by something that looks like an open tag
    # or inside one. A better way would be to use BeautifulSoup, but let's try a regex first.
    
    # Basic word boundary match for the names
    name_pattern = r'\b(' + '|'.join(re.escape(name) for name in sorted_names) + r')\b'
    
    # We'll use re.split to split the HTML into tags and text
    parts = re.split(r'(<[^>]+>)', html)
    result = []
    
    in_skip_tag = False
    skip_tags = {'a', 'code', 'pre', 'h1', 'h2', 'h3'}
    
    for part in parts:
        if part.startswith('<'):
            tag_name = part[1:].split()[0].replace('/', '').lower()
            if tag_name in skip_tags:
                if part.startswith('</'):
                    in_skip_tag = False
                else:
                    in_skip_tag = True
            result.append(part)
        else:
            if not in_skip_tag:
                # Apply auto-linking to the text content
                linked_text = re.sub(name_pattern, lambda m: f'<a href="{link_map[m.group(0)]}">{m.group(0)}</a>', part)
                result.append(linked_text)
            else:
                result.append(part)
                
    return "".join(result)

@app.get("/visualizations", response_class=HTMLResponse)
async def get_visualizations(request: Request):
    # 1. Timeline Chart
    timeline_data = data_loader.get_timeline_data()
    df_timeline = pd.DataFrame(timeline_data)
    
    # Sort for cleaner plotting
    df_timeline = df_timeline.sort_values('year')
    
    fig_timeline = px.scatter(
        df_timeline, 
        x="year", 
        y="influence_score",
        color="cluster",
        hover_name="name",
        size="influence_score",
        title="Programming Language Evolution & Influence",
        template="plotly_white",
        labels={"year": "Year of Creation", "influence_score": "Influence Score", "cluster": "Cluster"},
        height=600
    )
    
    fig_timeline.update_layout(
        font_family="Inter, sans-serif",
        title_font_size=24,
        margin=dict(l=40, r=40, t=80, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    timeline_html = fig_timeline.to_html(full_html=False, include_plotlyjs='cdn')

    # 2. Influence Network Graph
    influence_data = data_loader.get_influence_data()
    G = nx.DiGraph()
    for edge in influence_data:
        G.add_edge(edge['source'], edge['target'])
    
    # Layout the graph
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#cbd5e1'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    node_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="top center",
        marker=dict(
            showscale=True,
            colorscale='Blues',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    # Color nodes by number of connections
    node_adjacencies = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
    
    node_trace.marker.color = node_adjacencies

    fig_influence = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title='<br>Programming Language Influence Network',
                    titlefont_size=24,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    template="plotly_white",
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    
    influence_html = fig_influence.to_html(full_html=False, include_plotlyjs='cdn')

    return templates.TemplateResponse(
        "visualizations.html", 
        {
            "request": request, 
            "timeline_plot": timeline_html,
            "influence_plot": influence_html
        }
    )

@app.get("/api/viz/timeline")
async def api_viz_timeline():
    return data_loader.get_timeline_data()

@app.get("/api/viz/influence")
async def api_viz_influence():
    return data_loader.get_influence_data()

@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request, 
    sort: str = "year", 
    clusters: Optional[List[str]] = Query(None),
    paradigms: Optional[List[str]] = Query(None),
    min_year: int = 1930,
    max_year: int = 2024
):
    # Fetch filtered languages directly from SQL via DataLoader
    filtered_languages = data_loader.get_all_languages(
        clusters=clusters,
        paradigms=paradigms,
        min_year=min_year,
        max_year=max_year,
        sort=sort
    )
    
    available_clusters = data_loader.get_all_clusters()
    available_paradigms = data_loader.get_all_paradigms()

    context = {
        "request": request,
        "languages": filtered_languages, 
        "current_sort": sort,
        "available_clusters": available_clusters,
        "selected_clusters": clusters or [],
        "available_paradigms": available_paradigms,
        "selected_paradigms": paradigms or [],
        "min_year": min_year,
        "max_year": max_year,
        "min_bound": 1930,
        "max_bound": 2024
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("partials/language_grid.html", context)

    return templates.TemplateResponse("index.html", context)

@app.get("/compare", response_class=HTMLResponse)
async def compare_languages(request: Request, lang: List[str] = Query([]), lang1: Optional[str] = None, lang2: Optional[str] = None):
    # Support both multi-param 'lang' and specific 'lang1'/'lang2'
    selected = list(lang)
    if lang1: selected.append(lang1)
    if lang2: selected.append(lang2)
    
    # Remove duplicates and empty strings
    selected = list(dict.fromkeys([l for l in selected if l]))
    
    if not selected:
        return templates.TemplateResponse("compare.html", {"request": request, "languages": []})
    
    languages_data = data_loader.get_comparison_data(selected)
    
    return templates.TemplateResponse(
        "compare.html", 
        {"request": request, "languages": languages_data}
    )

@app.get("/compare/add")
async def add_to_compare(request: Request, lang: str):
    cookie_val = request.cookies.get("selected_languages", "")
    selected = [l for l in cookie_val.split(",") if l]
    if lang not in selected:
        selected.append(lang)
    
    response = templates.TemplateResponse(
        "partials/comparison_tray_content.html", 
        {"request": request, "selected_languages": selected}
    )
    response.set_cookie("selected_languages", ",".join(selected))
    return response

@app.get("/compare/remove")
async def remove_from_compare(request: Request, lang: str):
    cookie_val = request.cookies.get("selected_languages", "")
    selected = [l for l in cookie_val.split(",") if l and l != lang]
    
    response = templates.TemplateResponse(
        "partials/comparison_tray_content.html", 
        {"request": request, "selected_languages": selected}
    )
    response.set_cookie("selected_languages", ",".join(selected))
    return response

@app.get("/compare/clear")
async def clear_compare(request: Request):
    response = templates.TemplateResponse(
        "partials/comparison_tray_content.html", 
        {"request": request, "selected_languages": []}
    )
    response.delete_cookie("selected_languages")
    return response

@app.get("/compare/tray")
async def get_comparison_tray(request: Request):
    cookie_val = request.cookies.get("selected_languages", "")
    selected = [l for l in cookie_val.split(",") if l]
    return templates.TemplateResponse(
        "partials/comparison_tray_content.html", 
        {"request": request, "selected_languages": selected}
    )

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = Query("")):
    """Delegates to FTS5 layer and returns HTMX-compatible partials."""
    if not q or len(q) < 2:
        return ""
    
    # Perform FTS search via DataLoader
    results = data_loader.search(q)
    
    return templates.TemplateResponse(
        request=request,
        name="search_results.html",
        context={
            "results": results,
            "query": q
        }
    )

@app.get("/paradigm/{name}", response_class=HTMLResponse)
async def get_paradigm_view(request: Request, name: str, sort: str = "year"):
    info = data_loader.get_paradigm_info(name)
    all_languages = data_loader.get_all_languages()
    filtered_languages = [
        l for l in all_languages 
        if name.lower() in [p.lower() for p in (l.get('paradigms') or [])]
    ]
    
    if sort == "name":
        filtered_languages.sort(key=lambda x: x['name'].lower())
    else:
        filtered_languages.sort(key=lambda x: x.get('year', 0))
    
    return templates.TemplateResponse(
        request=request,
        name="tag_view.html",
        context={
            "type": "Paradigm",
            "info": info,
            "languages": filtered_languages,
            "current_sort": sort
        }
    )

@app.get("/cluster/{name}", response_class=HTMLResponse)
async def get_cluster_view(request: Request, name: str, sort: str = "year"):
    info = data_loader.get_cluster_info(name)
    all_languages = data_loader.get_all_languages()
    filtered_languages = [
        l for l in all_languages 
        if l.get('cluster', '').lower() == name.lower()
    ]
    
    if sort == "name":
        filtered_languages.sort(key=lambda x: x['name'].lower())
    else:
        filtered_languages.sort(key=lambda x: x.get('year', 0))
    
    return templates.TemplateResponse(
        request=request,
        name="tag_view.html",
        context={
            "type": "Cluster",
            "info": info,
            "languages": filtered_languages,
            "current_sort": sort
        }
    )

@app.get("/language/{name}", response_class=HTMLResponse)
async def get_language_profile(request: Request, name: str):
    lang = data_loader.get_combined_language_data(name)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    
    # Construct Markdown from the profile sections stored in the database
    # This replaces the need for the deleted docs/LANGUAGE_PROFILES directory
    content = f"# {lang.get('title', lang['name'])}\n\n"
    content += f"{lang.get('overview', '')}\n\n"
    
    # Core narrative sections
    sections = [
        ('philosophy', 'Philosophy'),
        ('historical_context', 'Historical Context'),
        ('mental_model', 'Mental Model'),
        ('key_innovations', 'Key Innovations'),
        ('tradeoffs', 'Tradeoffs'),
        ('legacy', 'Legacy'),
        ('ai_assisted_discovery_missions', 'AI Discovery Missions')
    ]
    
    for key, title in sections:
        val = lang.get(key)
        if val:
            content += f"## {title}\n"
            if isinstance(val, list):
                for item in val:
                    content += f"- {item}\n"
                content += "\n"
            else:
                content += f"{val}\n\n"
    
    html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
    html_content = auto_link_content(html_content)
    
    # Generate Dynamic Heritage Journey
    auto_odyssey = data_loader.get_auto_odyssey(lang['name'])
    
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "lang": lang, 
            "content": html_content, 
            "entity_type": "language",
            "auto_odyssey": auto_odyssey
        }
    )

@app.get("/person/{name}", response_class=HTMLResponse)
async def get_person_profile(request: Request, name: str):
    person = data_loader.get_person(name)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
        
    content = f"# {person.get('title', person.get('name', name))}\n\n"
    content += f"{person.get('overview', '')}\n\n"
    
    sections = [
        ('historical_context', 'Historical Context'),
        ('mental_model', 'Mental Model'),
        ('pivotal_works', 'Pivotal Works'),
        ('affiliations', 'Affiliations'),
        ('legacy', 'Legacy'),
        ('ai_assisted_discovery_missions', 'AI Discovery Missions')
    ]
    
    for key, title in sections:
        val = person.get(key)
        if val:
            content += f"## {title}\n"
            if isinstance(val, list):
                for item in val:
                    content += f"- {item}\n"
                content += "\n"
            else:
                content += f"{val}\n\n"
                
    html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
    html_content = auto_link_content(html_content)
    
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"lang": person, "content": html_content, "title": person.get('name', name), "entity_type": "person"}
    )

@app.get("/event/{slug}", response_class=HTMLResponse)
async def get_event_profile(request: Request, slug: str):
    event = data_loader.get_event(slug)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    content = f"# {event.get('title', slug)}\n\n"
    content += f"{event.get('overview', '')}\n\n"
    
    # Render sections
    sections = [
        ('impact_on_computing', 'Impact on Computing'),
        ('key_figures', 'Key Figures'),
        ('legacy', 'Legacy'),
        ('ai_assisted_discovery_missions', 'AI Discovery Missions')
    ]
    for key, title in sections:
        val = event.get(key)
        if val:
            content += f"## {title}\n"
            content += f"{val}\n\n"

    html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
    html_content = auto_link_content(html_content)
    
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"lang": event, "content": html_content, "title": event.get('title', slug), "entity_type": "event"}
    )

@app.get("/org/{name}", response_class=HTMLResponse)
async def get_org_profile(request: Request, name: str):
    org = data_loader.get_org(name)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    content = f"# {org.get('name', name)}\n\n"
    content += f"{org.get('overview', '')}\n\n"
    
    sections = [
        ('key_contributions', 'Key Contributions'),
        ('pivotal_people', 'Pivotal People'),
        ('legacy', 'Legacy'),
        ('ai_assisted_discovery_missions', 'AI Discovery Missions')
    ]
    for key, title in sections:
        val = org.get(key)
        if val:
            content += f"## {title}\n"
            content += f"{val}\n\n"

    html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
    html_content = auto_link_content(html_content)
    
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"lang": org, "content": html_content, "title": org.get('name', name), "entity_type": "org"}
    )

@app.get("/concept/{name}", response_class=HTMLResponse)
async def get_concept_profile_view(request: Request, name: str):
    concept = data_loader.get_concept_profile(name)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
        
    content = f"# {concept.get('title', name)}\n\n"
    content += f"{concept.get('overview', '')}\n\n"
    
    sections = [
        ('historical_context', 'Historical Context'),
        ('key_aspects', 'Key Aspects'),
        ('technical_implications', 'Technical Implications'),
        ('legacy', 'Legacy'),
        ('ai_assisted_discovery_missions', 'AI Discovery Missions')
    ]
    for key, title in sections:
        val = concept.get(key)
        if val:
            content += f"## {title}\n"
            content += f"{val}\n\n"

    html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
    html_content = auto_link_content(html_content)
    
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"lang": concept, "content": html_content, "title": concept.get('title', name), "entity_type": "concept"}
    )

@app.get("/odysseys", response_class=HTMLResponse)
async def list_odysseys_view(request: Request):
    odysseys = data_loader.get_learning_paths()
    return templates.TemplateResponse(
        request=request,
        name="odysseys.html",
        context={"odysseys": odysseys}
    )

@app.get("/odyssey/{path_id}", response_class=HTMLResponse)
async def get_odyssey_view(request: Request, path_id: str):
    path_data = data_loader.get_learning_path(path_id)
    if not path_data:
        raise HTTPException(status_code=404, detail="Odyssey not found")
    
    # Create a deep copy to avoid mutating the original data in the loader
    import copy
    path = copy.deepcopy(path_data)
    
    # Hydrate steps with additional data from profiles
    for step in path['steps']:
        lang_data = data_loader.get_combined_language_data(step['language'])
        if lang_data:
            # Use data from step if it exists (for custom rationales), otherwise fallback to profile
            raw_rationale = step.get('rationale') or lang_data.get('philosophy', 'Explore the unique philosophy of this language.')
            raw_challenge = step.get('challenge') or lang_data.get('challenge', 'Implement a core pattern using this language.')
            
            step['rationale'] = auto_link_content(markdown.markdown(raw_rationale))
            step['challenge'] = auto_link_content(markdown.markdown(raw_challenge))
            
            # Fetch AI Discovery Missions
            missions = lang_data.get('ai_assisted_discovery_missions', [])
            if isinstance(missions, str):
                missions = [missions]
            step['ai_missions'] = missions
            
            # Basic metadata for linking
            step['display_name'] = lang_data.get('display_name', step['language'])
            step['year'] = lang_data.get('year')
        else:
            step['display_name'] = step['language']
            step['rationale'] = auto_link_content(markdown.markdown(step.get('rationale', "Data not available for this language.")))
            step['challenge'] = auto_link_content(markdown.markdown(step.get('challenge', "Explore this language further.")))
            step['ai_missions'] = []

    return templates.TemplateResponse(
        request=request,
        name="odyssey_detail.html",
        context={"odyssey": path}
    )

@app.get("/narrative", response_class=HTMLResponse)
async def get_narrative_hub(request: Request):
    eras = data_loader.get_all_era_summaries()
    return templates.TemplateResponse(
        request=request,
        name="narrative_hub.html",
        context={"eras": eras}
    )

@app.get("/narrative/crossroads", response_class=HTMLResponse)
async def get_crossroads_view(request: Request):
    crossroads = data_loader.get_crossroads()
    
    # Render explanation Markdown
    for item in crossroads:
        item['explanation_html'] = markdown.markdown(item.get('explanation', ''), extensions=['extra', 'codehilite'])
        item['explanation_html'] = auto_link_content(item['explanation_html'])
        
    return templates.TemplateResponse(
        request=request,
        name="narrative_list.html",
        context={
            "title": "Historical Crossroads", 
            "items": crossroads, 
            "type": "crossroads",
            "description": "Pivotal moments that changed the direction of computer science."
        }
    )

@app.get("/narrative/reactions", response_class=HTMLResponse)
async def get_reactions_view(request: Request):
    reactions = data_loader.get_modern_reactions()
    
    # Render explanation Markdown
    for item in reactions:
        item['explanation_html'] = markdown.markdown(item.get('explanation', ''), extensions=['extra', 'codehilite'])
        item['explanation_html'] = auto_link_content(item['explanation_html'])
        
    return templates.TemplateResponse(
        request=request,
        name="narrative_list.html",
        context={
            "title": "Modern Reactions", 
            "items": reactions, 
            "type": "reactions",
            "description": "How the industry is responding to legacy constraints and new hardware realities."
        }
    )

@app.get("/narrative/era/{slug}", response_class=HTMLResponse)
async def get_era_view(request: Request, slug: str):
    era = data_loader.get_era_summary(slug)
    if not era:
        raise HTTPException(status_code=404, detail="Era not found")
        
    # Render Markdown fields
    era['overview_html'] = markdown.markdown(era.get('overview', ''), extensions=['extra', 'codehilite'])
    era['overview_html'] = auto_link_content(era['overview_html'])
    
    era['legacy_html'] = markdown.markdown(era.get('legacy_impact', ''), extensions=['extra', 'codehilite'])
    era['legacy_html'] = auto_link_content(era['legacy_html'])
    
    # Render list item descriptions
    for driver in era.get('key_drivers', []):
        driver['description_html'] = markdown.markdown(driver.get('description', ''), extensions=['extra'])
        driver['description_html'] = auto_link_content(driver['description_html'])
        
    for lang in era.get('pivotal_languages', []):
        lang['description_html'] = markdown.markdown(lang.get('description', ''), extensions=['extra'])
        lang['description_html'] = auto_link_content(lang['description_html'])

    return templates.TemplateResponse(
        request=request,
        name="era_view.html",
        context={"era": era}
    )

@app.get("/narrative/timeline", response_class=HTMLResponse)
async def get_timeline_narrative_view(request: Request):
    timeline = data_loader.get_timeline()
    
    # Render event descriptions
    for period in timeline:
        for event in period.get('events', []):
            event['description_html'] = markdown.markdown(event.get('description', ''), extensions=['extra', 'codehilite'])
            event['description_html'] = auto_link_content(event['description_html'])
            
    return templates.TemplateResponse(
        request=request,
        name="timeline_view.html",
        context={"timeline": timeline}
    )

@app.get("/narrative/concepts", response_class=HTMLResponse)
async def get_concepts_view(request: Request):
    concepts = data_loader.get_all_concepts()
    return templates.TemplateResponse(
        request=request,
        name="concepts_list.html",
        context={"concepts": concepts}
    )

# --- SEMANTIC SEARCH API ---

@app.get("/api")
async def api_index():
    """Returns documentation info for the API."""
    return {
        "title": "Language Atlas API",
        "description": "Programmatic access to the Language Atlas database.",
        "endpoints": {
            "/api/search?q={term}": "Semantic search (min 2 chars)",
            "/api/languages": "List all languages (with cluster/generation filters)",
            "/api/language/{name}": "Detailed language profile data",
            "/api/odysseys": "List all guided learning paths",
            "/api/odyssey/{id}": "Specific journey data and challenges"
        }
    }

@app.get("/api/search")
async def api_search(q: str = Query(...)):
    """Semantic search API for external consumers."""
    if len(q) < 2:
        return {"results": [], "query": q}
    results = data_loader.search(q)
    return {"results": results, "query": q}

@app.get("/api/languages")
async def api_list_languages(cluster: Optional[str] = None, generation: Optional[str] = None):
    """List languages with filters as JSON."""
    return data_loader.get_all_languages(filter_gen=generation, filter_cluster=cluster)

@app.get("/api/language/{name}")
async def api_get_language(name: str):
    """Get detailed language data as JSON."""
    lang = data_loader.get_combined_language_data(name)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    return lang

@app.get("/api/odysseys")
async def api_list_odysseys():
    """List all guided learning paths."""
    return data_loader.get_learning_paths()

@app.get("/api/people")
async def api_list_people():
    return data_loader.get_people_profiles()

@app.get("/api/person/{name}")
async def api_get_person(name: str):
    person = data_loader.get_person(name)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@app.get("/api/events")
async def api_list_events():
    return data_loader.get_historical_events()

@app.get("/api/event/{slug}")
async def api_get_event(slug: str):
    event = data_loader.get_event(slug)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@app.get("/api/odyssey/{path_id}")
async def api_get_odyssey(path_id: str):
    """Get a specific odyssey path."""
    path_data = data_loader.get_learning_path(path_id)
    if not path_data:
        raise HTTPException(status_code=404, detail="Odyssey not found")
        
    # Create a deep copy and hydrate
    import copy
    path = copy.deepcopy(path_data)
    for step in path['steps']:
        lang_data = data_loader.get_combined_language_data(step['language'])
        if lang_data:
            step['challenge'] = lang_data.get('challenge', 'No specific challenge listed.')
            
    return path

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8084, reload=True)
