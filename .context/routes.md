# Routes & API

**Server:** `src/app/app.py` — FastAPI, port 8084
**HTMX partials:** requests with `HX-Request` header return partial templates

## Static Export Behavior

`SiteCrawler` fetches every crawlable route via `TestClient` and writes the
rendered HTML to `site/`. The crawl always runs without query parameters, so
exported pages reflect the default (unfiltered) server state.

At runtime in the browser, `src/app/static/atlas-static.js` loads the
SQLite database client-side (via sql.js-httpvfs) and wires two behaviors:

- **Filter form** (`form[hx-get]`): `change` events run live SQL queries and
  re-render the language grid, replacing the HTMX mechanism entirely.
- **Search box**: input triggers a client-side FTS5 query instead of hitting
  the server.

So "filter form inert" in the table below means the crawled HTML is the
unfiltered state; it does not mean filters are broken in the deployed site.
Routes marked **skipped** are not exported at all.

## Web Routes (HTML)

"Static export" column: **crawled** = emitted by `SiteCrawler` into `site/`; **skipped** = not exported (POST, cookie mutator, HTMX partial, or JSON-only).

| Route | Template | Notes | Static export |
|---|---|---|---|
| `GET /` | `index.html` / `partials/language_grid.html` | Filter by cluster, paradigms, year; HTMX partial replaced by atlas-static.js at runtime | crawled (unfiltered state; filters functional via client-side SQL) |
| `GET /compare` | `compare.html` | lang, lang1, lang2 params | crawled (empty state) |
| `GET /compare/add` | `partials/comparison_tray_content.html` | Sets cookie | skipped |
| `GET /compare/remove` | `partials/comparison_tray_content.html` | Modifies cookie | skipped |
| `GET /compare/clear` | `partials/comparison_tray_content.html` | Deletes cookie | skipped |
| `GET /compare/tray` | `partials/comparison_tray_content.html` | Reads cookie | skipped |
| `GET /search` | `search_results.html` | FTS5 search, q param (min 2 chars) | skipped (needs query) |
| `GET /language/{name}` | `profile.html` | shared language-like profile route; preserves stored `entity_type` for `language`, `foundation`, and `artifact` records; auto-link Markdown; groups upstream influences into foundational precursors, language ancestors, and optional artifact/runtime influences using upstream `entity_type` data; profile now includes deep ancestry (depth >= 2), notable descendants, and graph role section using closure table data injected at route handler time | crawled |
| `GET /person/{name}` | `profile.html` | entity_type=person | crawled |
| `GET /event/{slug}` | `profile.html` | entity_type=event | crawled |
| `GET /org/{name}` | `profile.html` | entity_type=org | crawled |
| `GET /concept/{name}` | `profile.html` | entity_type=concept | crawled |
| `GET /paradigm/{name}` | `paradigm_view.html` | foundation-aware ecosystem view with ranked precursors and sorted language cards | crawled |
| `GET /cluster/{name}` | `tag_view.html` | type=Cluster | crawled |
| `GET /odysseys` | `odysseys.html` | | crawled |
| `GET /odyssey/{path_id}` | `odyssey_detail.html` | hydrates steps with language profiles | crawled |
| `GET /narrative` | `narrative_hub.html` | eras hub | crawled |
| `GET /narrative/crossroads` | `narrative_list.html` | type=crossroads | crawled |
| `GET /narrative/reactions` | `narrative_list.html` | type=reactions | crawled |
| `GET /narrative/era/{slug}` | `era_view.html` | | crawled |
| `GET /narrative/timeline` | `timeline_view.html` | | crawled |
| `GET /narrative/concepts` | `concepts_list.html` | | crawled |
| `GET /lineage/{language_id}` | HTMLResponse (inline) | Plotly lineage graph | crawled |
| `GET /insights` | `insights.html` | window function analytics | crawled |
| `GET /visualizations` | `visualizations.html` | Plotly timeline + influence network | crawled |
| `GET /api` | API index / docs | JSON | skipped |

## JSON API Routes
| Route | Notes |
|---|---|
| `GET /api` | API index / docs |
| `GET /api/search?q=` | FTS5 search → {results, query} |
| `GET /api/languages` | cluster, generation, sort, min_year, max_year filters |
| `GET /api/language/{name}` | Combined profile; preserves flat influence lists and adds grouped upstream detail fields for profile-aware clients. CLI dashboard / influences views and the TUI reader / nexus now rely on these grouped fields when present. |
| `GET /api/lineage/{name}` | Full transitive lineage from closure tables; ancestors and descendants sorted by depth |
| `GET /api/path?from=X&to=Y` | Shortest influence path between two languages; returns reachable/min_depth/sample_paths |
| `GET /api/reports/keystones` | Keystone entities report; returns 503 if make derived-data has not run |
| `GET /api/reports/bridges` | Bridge entities report; same 503 behavior |
| `GET /api/reports/orphans` | Orphan subgraph report; same 503 behavior |
| `GET /api/paradigms` | List |
| `GET /api/paradigm/{name}` | Detail |
| `GET /api/paradigm/{name}/ecosystem` | Foundation-aware paradigm ecosystem payload used by the web route and mirrored by the CLI `atlas paradigm` surface |
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
| `GET /api/viz/influence-expanded` | Expanded influence graph with closure context; same 503 behavior |
| `GET /api/insights/momentum` | Paradigm momentum data |

## Templates Directory
```
src/app/templates/
  base.html                          # Base layout
  index.html                         # Language grid + filters
  profile.html                       # Universal entity profile; `/language/{name}` is shared by language-like entities and renders typed upstream influence groups
  compare.html                       # Side-by-side comparison
  tag_view.html                      # Generic cluster filtered view
  paradigm_view.html                 # Foundation-aware paradigm ecosystem view
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

## Terminal Navigation Notes

- The CLI now has a dedicated paradigm ecosystem entry point: `atlas paradigm <name>`.
- The TUI chronology pane remains language-first by default, but `m` cycles browse mode through languages, foundations, artifacts, and all language-like entities so mixed-corpus navigation stays explicit.
