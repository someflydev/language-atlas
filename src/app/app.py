import os
import re
import copy
import markdown
import sqlite3
import polars as pl
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from typing import List, Optional, Dict, Any, Union, AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.data_loader import DataLoader
import uvicorn

# Ensure SQLite mode is enabled for DataLoader
os.environ['USE_SQLITE'] = '1'

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Establish a read-only SQLite connection on startup
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'language_atlas.sqlite'))
    if not os.path.exists(db_path):
        print(f"CRITICAL: Database not found at {db_path}")
    
    # We could attach a pool here if needed, but for now DataLoader handles its own connections
    yield

app = FastAPI(title="Language Atlas", lifespan=lifespan)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Expose ATLAS_STATIC_MODE to all templates as a callable so it is
# evaluated at render time, not at import time.  The SiteCrawler sets
# this env var before making requests; clearing it on exit restores the
# normal live-app behaviour.
templates.env.globals["atlas_static_mode"] = lambda: os.environ.get("ATLAS_STATIC_MODE", "0") == "1"


def atlas_static_mode() -> bool:
    return os.environ.get("ATLAS_STATIC_MODE", "0") == "1"

# Initialize data loader
data_loader = DataLoader()

# Global entity link map for auto-linking
_entity_link_map: Optional[Dict[str, str]] = None

def get_link_map() -> Dict[str, str]:
    global _entity_link_map
    if _entity_link_map is None:
        _entity_link_map = data_loader.get_entity_link_map()
    return _entity_link_map or {}

def auto_link_content(html: str) -> str:
    """Automatically wraps known entity names with HTML links, avoiding existing tags."""
    link_map = get_link_map()
    if not link_map:
        return html
    
    # Names to look for, sorted by length descending
    sorted_names = sorted(link_map.keys(), key=len, reverse=True)
    
    # Regex to match names NOT inside <a> or <code> or <pre> tags
    # Basic word boundary match for the names
    name_pattern = r'\b(' + '|'.join(re.escape(name) for name in sorted_names) + r')\b'
    
    # We'll use re.split to split the HTML into tags and text
    parts = re.split(r'(<[^>]+>)', html)
    result: List[str] = []
    
    in_skip_tag = False
    skip_tags = {'a', 'code', 'pre', 'h1', 'h2', 'h3'}
    
    for part in parts:
        if part.startswith('<'):
            tag_name_match = re.match(r'</?([a-z0-9]+)', part.lower())
            if tag_name_match:
                tag_name = tag_name_match.group(1)
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

# --- Exception Handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request=request,
            name="errors/404.html", 
            context={"detail": exc.detail}, 
            status_code=404
        )
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc: Exception) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="errors/500.html", 
        context={"detail": "Internal Server Error"}, 
        status_code=500
    )

@app.get("/visualizations", response_class=HTMLResponse)
async def get_visualizations(request: Request) -> Response:
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
    
    edge_x: List[Optional[float]] = []
    edge_y: List[Optional[float]] = []
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

    node_x: List[float] = []
    node_y: List[float] = []
    node_text: List[str] = []
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
            ),
            line_width=2))

    # Color nodes by number of connections
    node_adjacencies: List[int] = []
    for node in G.nodes():
        node_adjacencies.append(len(list(G.neighbors(node))))
    
    node_trace.marker.color = node_adjacencies

    fig_influence = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title='<br>Programming Language Influence Network',
                    title_font_size=24,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    template="plotly_white",
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    
    influence_html = fig_influence.to_html(full_html=False, include_plotlyjs='cdn')

    return templates.TemplateResponse(
        request=request,
        name="visualizations.html", 
        context={
            "timeline_plot": timeline_html,
            "influence_plot": influence_html
        }
    )

@app.get("/api/viz/timeline")
async def api_viz_timeline() -> List[Dict[str, Any]]:
    return data_loader.get_timeline_data()

@app.get("/api/viz/influence")
async def api_viz_influence() -> Any:
    return data_loader.get_influence_data()

@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request, 
    sort: str = "year", 
    clusters: Optional[List[str]] = Query(None),
    paradigms: Optional[List[str]] = Query(None),
    min_year: int = 1930,
    max_year: int = 2024
) -> Response:
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
        return templates.TemplateResponse(request=request, name="partials/language_grid.html", context=context)

    return templates.TemplateResponse(request=request, name="index.html", context=context)

@app.get("/compare", response_class=HTMLResponse)
async def compare_languages(
    request: Request, 
    lang: List[str] = Query([]), 
    lang1: Optional[str] = None, 
    lang2: Optional[str] = None
) -> Response:
    # Support both multi-param 'lang' and specific 'lang1'/'lang2'
    selected = list(lang)
    if lang1: selected.append(lang1)
    if lang2: selected.append(lang2)
    
    # Remove duplicates and empty strings
    selected = list(dict.fromkeys([l for l in selected if l]))
    
    if not selected:
        return templates.TemplateResponse(
            request=request,
            name="compare.html", 
            context={"languages": []}
        )
    
    languages_data = data_loader.get_comparison_data(selected)
    
    return templates.TemplateResponse(
        request=request,
        name="compare.html", 
        context={"languages": languages_data}
    )

@app.get("/compare/add")
async def add_to_compare(request: Request, lang: str) -> Response:
    cookie_val = request.cookies.get("selected_languages", "")
    selected = [l for l in cookie_val.split(",") if l]
    if lang not in selected:
        selected.append(lang)
    
    response = templates.TemplateResponse(
        request=request,
        name="partials/comparison_tray_content.html", 
        context={"selected_languages": selected}
    )
    response.set_cookie("selected_languages", ",".join(selected))
    return response

@app.get("/compare/remove")
async def remove_from_compare(request: Request, lang: str) -> Response:
    cookie_val = request.cookies.get("selected_languages", "")
    selected = [l for l in cookie_val.split(",") if l and l != lang]
    
    response = templates.TemplateResponse(
        request=request,
        name="partials/comparison_tray_content.html", 
        context={"selected_languages": selected}
    )
    response.set_cookie("selected_languages", ",".join(selected))
    return response

@app.get("/compare/clear")
async def clear_compare(request: Request) -> Response:
    response = templates.TemplateResponse(
        request=request,
        name="partials/comparison_tray_content.html", 
        context={"selected_languages": []}
    )
    response.delete_cookie("selected_languages")
    return response

@app.get("/compare/tray")
async def get_comparison_tray(request: Request) -> Response:
    cookie_val = request.cookies.get("selected_languages", "")
    selected = [l for l in cookie_val.split(",") if l]
    return templates.TemplateResponse(
        request=request,
        name="partials/comparison_tray_content.html", 
        context={"selected_languages": selected}
    )

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = Query("")) -> Any:
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
async def get_paradigm_view(request: Request, name: str, sort: str = "year") -> Response:
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
async def get_cluster_view(request: Request, name: str, sort: str = "year") -> Response:
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
async def get_language_profile(request: Request, name: str) -> Response:
    lang = data_loader.get_combined_language_data(name)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    
    # Construct Markdown from the profile sections stored in the database
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

    # Static export crawls every language page, so skip the expensive
    # lineage view queries there and keep the live app unchanged.
    if atlas_static_mode():
        ancestors: list[dict[str, Any]] = []
        descendants: list[dict[str, Any]] = []
        lang_rank: dict[str, Any] | None = None
    else:
        ancestors = data_loader.get_ancestors(lang['id'], max_depth=5)
        descendants = data_loader.get_descendants(lang['id'], max_depth=5)
        lang_rank = data_loader.get_language_ranking(lang['id'])
    
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "lang": lang, 
            "content": html_content, 
            "entity_type": "language",
            "auto_odyssey": auto_odyssey,
            "ancestors": ancestors,
            "descendants": descendants,
            "ranking": lang_rank
        }
    )

@app.get("/person/{name}", response_class=HTMLResponse)
async def get_person_profile(request: Request, name: str) -> Response:
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
async def get_event_profile(request: Request, slug: str) -> Response:
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
async def get_org_profile(request: Request, name: str) -> Response:
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
async def get_concept_profile_view(request: Request, name: str) -> Response:
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
async def list_odysseys_view(request: Request) -> Response:
    odysseys = data_loader.get_learning_paths()
    return templates.TemplateResponse(
        request=request,
        name="odysseys.html",
        context={"odysseys": odysseys}
    )

@app.get("/odyssey/{path_id}", response_class=HTMLResponse)
async def get_odyssey_view(request: Request, path_id: str) -> Response:
    path_data = data_loader.get_learning_path(path_id)
    if not path_data:
        raise HTTPException(status_code=404, detail="Odyssey not found")
    
    # Create a deep copy to avoid mutating the original data in the loader
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
async def get_narrative_hub(request: Request) -> Response:
    eras = data_loader.get_all_era_summaries()
    return templates.TemplateResponse(
        request=request,
        name="narrative_hub.html",
        context={"eras": eras}
    )

@app.get("/narrative/crossroads", response_class=HTMLResponse)
async def get_crossroads_view(request: Request) -> Response:
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
async def get_reactions_view(request: Request) -> Response:
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
async def get_era_view(request: Request, slug: str) -> Response:
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
async def get_timeline_narrative_view(request: Request) -> Response:
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
async def get_concepts_view(request: Request) -> Response:
    concepts = data_loader.get_all_concepts()
    return templates.TemplateResponse(
        request=request,
        name="concepts_list.html",
        context={"concepts": concepts}
    )

@app.get("/lineage/{language_id}", response_class=HTMLResponse)
async def get_lineage_visualization(request: Request, language_id: int) -> Response:
    ancestors = data_loader.get_ancestors(language_id, max_depth=5)
    descendants = data_loader.get_descendants(language_id, max_depth=5)
    
    # Construct graph data
    G = nx.DiGraph()
    
    # Query root name
    conn = data_loader._get_connection()
    try:
        cursor = conn.execute("SELECT name FROM languages WHERE id = ?", (language_id,))
        row = cursor.fetchone()
        root_name = row['name'] if row else f"Language {language_id}"
    finally:
        conn.close()

    G.add_node(root_name)
    
    # Process ancestors (they point towards root or its parents)
    for anc in ancestors:
        path = anc['path']
        parts = path.split(' <- ')
        for i in range(len(parts) - 1):
            G.add_edge(parts[i+1], parts[i])
            
    # Process descendants
    for desc in descendants:
        path = desc['path']
        parts = path.split(' -> ')
        for i in range(len(parts) - 1):
            G.add_edge(parts[i], parts[i+1])

    if not G.nodes or len(G.nodes) == 1:
        return HTMLResponse("No lineage data found for this language.")

    pos = nx.spring_layout(G, k=0.5, iterations=50)
    
    edge_x: List[Optional[float]] = []
    edge_y: List[Optional[float]] = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#cbd5e1'),
        hoverinfo='none',
        mode='lines')

    node_x: List[float] = []
    node_y: List[float] = []
    node_text: List[str] = []
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
            color=['#3b82f6' if node == root_name else '#94a3b8' for node in G.nodes()],
            size=[15 if node == root_name else 10 for node in G.nodes()],
            line_width=2))

    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title=f'<br>Deep Lineage: {root_name}',
                    title_font_size=24,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    template="plotly_white",
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    
    html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    # Wrap in our standard layout
    page_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lineage: {root_name}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-50 min-h-screen p-8 font-sans">
        <div class="max-w-6xl mx-auto bg-white rounded-3xl shadow-sm border border-slate-100 p-8">
            <a href="/language/{{root_name}}" class="inline-flex items-center text-sm font-bold text-slate-400 hover:text-blue-600 mb-6 uppercase tracking-wide">
                &larr; Back to Profile
            </a>
            <div class="w-full h-[700px]">
                {{html}}
            </div>
        </div>
    </body>
    </html>
    '''
    return HTMLResponse(content=page_html)

@app.get("/people", response_class=HTMLResponse)
async def list_people_view(request: Request) -> Response:
    people = data_loader.get_people_list()
    return templates.TemplateResponse(
        request=request,
        name="people_list.html",
        context={"people": people}
    )

@app.get("/orgs", response_class=HTMLResponse)
async def list_orgs_view(request: Request) -> Response:
    orgs = data_loader.get_orgs_list()
    return templates.TemplateResponse(
        request=request,
        name="orgs_list.html",
        context={"orgs": orgs}
    )

@app.get("/events", response_class=HTMLResponse)
async def list_events_view(request: Request) -> Response:
    events = data_loader.get_events_list()
    return templates.TemplateResponse(
        request=request,
        name="events_list.html",
        context={"events": events}
    )

@app.get("/insights", response_class=HTMLResponse)
async def get_insights(request: Request) -> Response:
    rankings = data_loader.get_top_languages_by_era()
    momentum = data_loader.get_paradigm_momentum_timeline()
    
    # Generate the momentum chart using Plotly
    import pandas as pd
    import plotly.express as px
    
    if momentum:
        df_momentum = pd.DataFrame(momentum)
        # Sort values
        df_momentum = df_momentum.sort_values(['year', 'paradigm_name'])
        
        fig_momentum = px.line(
            df_momentum,
            x="year",
            y="cumulative_languages",
            color="paradigm_name",
            title="Rolling Momentum of Paradigms",
            template="plotly_white",
            labels={"year": "Year", "cumulative_languages": "Cumulative Languages", "paradigm_name": "Paradigm"}
        )
        
        fig_momentum.update_layout(
            font_family="Inter, sans-serif",
            title_font_size=24,
            margin=dict(l=40, r=40, t=80, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        momentum_chart_html = fig_momentum.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        momentum_chart_html = "<p>No data available.</p>"

    # Group rankings by generation for the template
    grouped_rankings: dict[str, list[dict[str, Any]]] = {}
    for r in rankings:
        gen = r.get('generation')
        if not gen:
            continue
        if gen not in grouped_rankings:
            grouped_rankings[gen] = []
        # only keep top 5 per generation
        if r.get('generation_rank', 99) <= 5:
            grouped_rankings[gen].append(r)

    # sort the lists by generation_rank
    for gen in grouped_rankings:
        grouped_rankings[gen].sort(key=lambda x: x.get('generation_rank', 99))

    return templates.TemplateResponse(
        request=request,
        name="insights.html",
        context={
            "grouped_rankings": grouped_rankings,
            "momentum_chart": momentum_chart_html
        }
    )

@app.get("/api/insights/momentum")
async def api_insights_momentum() -> Any:
    return data_loader.get_paradigm_momentum_timeline()

# --- SEMANTIC SEARCH API ---

@app.get("/api")
async def api_index() -> Dict[str, Any]:
    """Returns documentation info for the API."""
    return {
        "title": "Language Atlas API",
        "description": "Programmatic access to the Language Atlas database.",
        "endpoints": {
            "/api/search?q={term}": "Semantic search (min 2 chars)",
            "/api/languages": "List all languages (with cluster, generation, sort, min_year, max_year filters)",
            "/api/language/{name}": "Detailed language profile data",
            "/api/paradigms": "List all programming paradigms",
            "/api/paradigm/{name}": "Detailed paradigm information",
            "/api/concepts": "List all programming concepts",
            "/api/concept/{name}": "Detailed concept profile data",
            "/api/eras": "List all historical eras of computing",
            "/api/era/{slug}": "Detailed era summary and narrative",
            "/api/organizations": "List all organization profiles",
            "/api/org/{name}": "Detailed organization information",
            "/api/people": "List all people profiles",
            "/api/person/{name}": "Detailed person profile data",
            "/api/historical_events": "List all historical events",
            "/api/event/{slug}": "Detailed historical event data",
            "/api/odysseys": "List all guided learning paths",
            "/api/odyssey/{id}": "Specific journey data and challenges"
        }
    }

@app.get("/api/search")
async def api_search(q: str = Query(...)) -> Dict[str, Any]:
    """Semantic search API for external consumers."""
    if len(q) < 2:
        return {"results": [], "query": q}
    results = data_loader.search(q)
    return {"results": results, "query": q}

@app.get("/api/languages")
async def api_list_languages(
    cluster: Optional[str] = None, 
    generation: Optional[str] = None,
    sort: str = "year",
    min_year: int = 1930,
    max_year: int = 2024
) -> Any:
    """List languages with filters as JSON."""
    return data_loader.get_all_languages(
        filter_gen=generation, 
        filter_cluster=cluster,
        sort=sort,
        min_year=min_year,
        max_year=max_year
    )

@app.get("/api/language/{name}")
async def api_get_language(name: str) -> Any:
    """Get detailed language data as JSON."""
    lang = data_loader.get_combined_language_data(name)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    return lang

@app.get("/api/paradigms")
async def api_list_paradigms() -> Any:
    """List all paradigms."""
    return data_loader.get_all_paradigms()

@app.get("/api/paradigm/{name}")
async def api_get_paradigm(name: str) -> Any:
    """Get paradigm detail."""
    return data_loader.get_paradigm_info(name)

@app.get("/api/concepts")
async def api_list_concepts() -> Any:
    """List all concepts."""
    return data_loader.get_all_concepts()

@app.get("/api/concept/{name}")
async def api_get_concept(name: str) -> Any:
    """Get concept detail."""
    concept = data_loader.get_concept_profile(name)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    return concept

@app.get("/api/eras")
async def api_list_eras() -> Any:
    """List all era summaries."""
    return data_loader.get_all_era_summaries()

@app.get("/api/era/{slug}")
async def api_get_era(slug: str) -> Any:
    """Get era summary detail."""
    era = data_loader.get_era_summary(slug)
    if not era:
        raise HTTPException(status_code=404, detail="Era not found")
    return era

@app.get("/api/organizations")
async def api_list_organizations() -> Any:
    """List all organization profiles."""
    return data_loader.get_org_profiles()

@app.get("/api/org/{name}")
async def api_get_org(name: str) -> Any:
    """Get organization detail."""
    org = data_loader.get_org(name)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@app.get("/api/odysseys")
async def api_list_odysseys() -> Any:
    """List all guided learning paths."""
    return data_loader.get_learning_paths()

@app.get("/api/people")
async def api_list_people() -> Any:
    return data_loader.get_people_profiles()

@app.get("/api/person/{name}")
async def api_get_person(name: str) -> Any:
    person = data_loader.get_person(name)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@app.get("/api/historical_events")
async def api_list_historical_events() -> Any:
    return data_loader.get_historical_events()

@app.get("/api/event/{slug}")
async def api_get_event(slug: str) -> Any:
    event = data_loader.get_event(slug)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@app.get("/api/odyssey/{path_id}")
async def api_get_odyssey(path_id: str) -> Any:
    """Get a specific odyssey path."""
    path_data = data_loader.get_learning_path(path_id)
    if not path_data:
        raise HTTPException(status_code=404, detail="Odyssey not found")
        
    # Create a deep copy and hydrate
    path = copy.deepcopy(path_data)
    for step in path['steps']:
        lang_data = data_loader.get_combined_language_data(step['language'])
        if lang_data:
            step['challenge'] = lang_data.get('challenge', 'No specific challenge listed.')
            
    return path

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8084, reload=True)
