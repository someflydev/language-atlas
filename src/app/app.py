import os
import markdown
import sqlite3
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

# Initialize data loader
data_loader = DataLoader()

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
    
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"lang": lang, "content": html_content}
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
    
    # Hydrate steps with challenges from profiles
    for step in path['steps']:
        lang_data = data_loader.get_combined_language_data(step['language'])
        if lang_data:
            step['challenge'] = lang_data.get('challenge', 'No specific challenge listed.')

    return templates.TemplateResponse(
        request=request,
        name="odyssey_detail.html",
        context={"odyssey": path}
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
