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
    all_languages = data_loader.get_all_languages()
    available_clusters = data_loader.get_all_clusters()
    available_paradigms = data_loader.get_all_paradigms()

    filtered_languages = all_languages

    # Filter by clusters
    if clusters:
        filtered_languages = [l for l in filtered_languages if l.get('cluster') in clusters]
    
    # Filter by paradigms
    if paradigms:
        filtered_languages = [
            l for l in filtered_languages 
            if any(p in (l.get('paradigms') or []) for p in paradigms)
        ]
    
    # Filter by year range
    filtered_languages = [
        l for l in filtered_languages 
        if min_year <= l.get('year', 0) <= max_year
    ]

    # Sort the results
    if sort == "name":
        filtered_languages.sort(key=lambda x: x['name'].lower())
    else:
        filtered_languages.sort(key=lambda x: x.get('year', 0))

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
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
    lang = data_loader.get_language(name)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    
    # Path to markdown profile
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    profile_path = os.path.join(base_dir, 'docs', 'LANGUAGE_PROFILES', f"{name}.md")
    
    if not os.path.exists(profile_path):
        content = f"# {name}\n\nProfile documentation is coming soon."
    else:
        with open(profile_path, 'r') as f:
            content = f.read()
    
    html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
    
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"lang": lang, "content": html_content}
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8084, reload=True)
