# Routes & API

**Server:** `src/app/app.py` — FastAPI, port 8084
**HTMX partials:** requests with `HX-Request` header return partial templates

## Web Routes (HTML)
| Route | Template | Notes |
|---|---|---|
| `GET /` | `index.html` / `partials/language_grid.html` | Filter by cluster, paradigms, year; HTMX partial |
| `GET /compare` | `compare.html` | lang, lang1, lang2 params |
| `GET /compare/add` | `partials/comparison_tray_content.html` | Sets cookie |
| `GET /compare/remove` | `partials/comparison_tray_content.html` | Modifies cookie |
| `GET /compare/clear` | `partials/comparison_tray_content.html` | Deletes cookie |
| `GET /compare/tray` | `partials/comparison_tray_content.html` | Reads cookie |
| `GET /search` | `search_results.html` | FTS5 search, q param (min 2 chars) |
| `GET /language/{name}` | `profile.html` | entity_type=language; auto-link Markdown |
| `GET /person/{name}` | `profile.html` | entity_type=person |
| `GET /event/{slug}` | `profile.html` | entity_type=event |
| `GET /org/{name}` | `profile.html` | entity_type=org |
| `GET /concept/{name}` | `profile.html` | entity_type=concept |
| `GET /paradigm/{name}` | `tag_view.html` | type=Paradigm |
| `GET /cluster/{name}` | `tag_view.html` | type=Cluster |
| `GET /odysseys` | `odysseys.html` | |
| `GET /odyssey/{path_id}` | `odyssey_detail.html` | hydrates steps with language profiles |
| `GET /narrative` | `narrative_hub.html` | eras hub |
| `GET /narrative/crossroads` | `narrative_list.html` | type=crossroads |
| `GET /narrative/reactions` | `narrative_list.html` | type=reactions |
| `GET /narrative/era/{slug}` | `era_view.html` | |
| `GET /narrative/timeline` | `timeline_view.html` | |
| `GET /narrative/concepts` | `concepts_list.html` | |
| `GET /lineage/{language_id}` | HTMLResponse (inline) | Plotly lineage graph |
| `GET /insights` | `insights.html` | window function analytics |
| `GET /visualizations` | `visualizations.html` | Plotly timeline + influence network |

## JSON API Routes
| Route | Notes |
|---|---|
| `GET /api` | API index / docs |
| `GET /api/search?q=` | FTS5 search → {results, query} |
| `GET /api/languages` | cluster, generation, sort, min_year, max_year filters |
| `GET /api/language/{name}` | Combined profile |
| `GET /api/paradigms` | List |
| `GET /api/paradigm/{name}` | Detail |
| `GET /api/concepts` | List |
| `GET /api/concept/{name}` | Detail |
| `GET /api/eras` | List |
| `GET /api/era/{slug}` | Detail |
| `GET /api/organizations` | All org profiles |
| `GET /api/org/{name}` | Detail |
| `GET /api/people` | All people profiles |
| `GET /api/person/{name}` | Detail |
| `GET /api/historical_events` | All |
| `GET /api/event/{slug}` | Detail |
| `GET /api/odysseys` | List |
| `GET /api/odyssey/{id}` | Detail + hydrated steps |
| `GET /api/viz/timeline` | Raw timeline data |
| `GET /api/viz/influence` | Raw influence edges |
| `GET /api/insights/momentum` | Paradigm momentum data |

## Templates Directory
```
src/app/templates/
  base.html                          # Base layout
  index.html                         # Language grid + filters
  profile.html                       # Universal entity profile (language/person/event/org/concept)
  compare.html                       # Side-by-side comparison
  tag_view.html                      # Paradigm/cluster filtered view
  insights.html                      # Analytics dashboard
  visualizations.html                # Plotly charts
  narrative_hub.html                 # Era/crossroads navigation
  narrative_list.html                # Crossroads / modern reactions list
  era_view.html                      # Single era narrative
  timeline_view.html                 # Historical timeline
  concepts_list.html                 # All concepts
  odysseys.html                      # Learning paths list
  odyssey_detail.html                # Single guided odyssey
  search_results.html                # FTS5 search results
  partials/
    language_grid.html               # HTMX language card grid
    comparison_tray_content.html     # Cookie-driven compare tray
    comparison_table.html            # Full comparison table
  errors/
    404.html
    500.html
```
