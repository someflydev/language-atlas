# Language Atlas API Reference

The Language Atlas provides a RESTful API for programmatic access to programming language history, influences, and guided learning paths (Odysseys).

## Base URL
The API is exposed via the FastAPI web interface (default: `http://localhost:8084/api`).

## Interactive Documentation

FastAPI exposes two auto-generated documentation UIs at the following URLs
while the server is running:

- `http://localhost:8084/docs` — Swagger UI (try endpoints in-browser)
- `http://localhost:8084/redoc` — ReDoc (clean reference view)
- `http://localhost:8084/openapi.json` — raw OpenAPI 3 schema

---

## Endpoints

### 0. API Index

A machine-readable directory of all available endpoints.

- **URL:** `/api`
- **Method:** `GET`
- **Response:**
  ```json
  {
    "title": "Language Atlas API",
    "description": "Programmatic access to the Language Atlas database.",
    "endpoints": {
      "/api/search?q={term}": "Semantic search (min 2 chars)",
      "/api/languages": "List all languages (with filters)",
      "/api/entity-types": "Counts grouped by entity_type",
      "/api/language/{name}": "Detailed language profile data",
      "/api/lineage/{name}": "Full transitive lineage from closure tables",
      "/api/path?from={source}&to={target}": "Shortest influence path between two languages",
      "/api/reports/keystones": "Keystone entities report",
      "/api/reports/bridges": "Bridge entities report",
      "/api/reports/orphans": "Orphan subgraph report",
      "/api/viz/influence-expanded": "Expanded influence graph with closure context"
    }
  }
  ```

### 1. Language Browser (HTML)
The main Atlas browser also supports entity-type filtering on the HTML route.

- **URL:** `/languages`
- **Method:** `GET`
- **Query Params:**
  - `entity_type`: `language` (default), `foundation`, or `artifact`.
  - `cluster`: Filter by cluster within the selected entity type.
  - `sort`: `year` (default) or `name`.
  - `min_year`: Integer (default: 1800 on `/languages`).
  - `max_year`: Integer (default: 2024).

### 2. Semantic Search
Perform a full-text search across languages, profiles, and concepts using FTS5 ranking.

- **URL:** `/api/search`
- **Method:** `GET`
- **Query Params:** `q` (search term, min 2 chars)
- **Response:**
  ```json
  {
    "results": [
      {
        "category": "language",
        "title": "Rust",
        "snippet": "...memory safety without a <b>garbage collector</b>...",
        "score": -1.25,
        "language_id": 45
      }
    ],
    "query": "garbage collector"
  }
  ```

### 3. List Languages
Retrieve a list of all languages with optional filtering and sorting.

- **URL:** `/api/languages`
- **Method:** `GET`
- **Query Params:** 
  - `cluster`: Filter by functional domain. Options: `AI`, `academic`, `backend`, `business`, `cloud`, `data`, `education`, `enterprise`, `finance`, `frontend`, `historical`, `infra`, `mathematics`, `safety-critical`, `scientific`, `scripting`, `systems`, `web`.
  - `generation`: Filter by era/generation. Options: `dawn`, `early`, `web1`, `cloud`, `renaissance`, `autonomic`.
  - `entity_type`: `language` (default), `foundation`, or `artifact`.
  - `sort`: `year` (default) or `name`.
  - `min_year`: Integer (default: 1930).
  - `max_year`: Integer (default: 2024).
- **Response:** Array of language objects.

### 4. Entity Type Summary
Retrieve the current counts of language-like entities grouped by `entity_type`.

- **URL:** `/api/entity-types`
- **Method:** `GET`
- **Response:**
  ```json
  {
    "entity_types": {
      "artifact": 15,
      "foundation": 12,
      "language": 126
    }
  }
  ```

### 5. Get Language Detail
Retrieve core data and extended profile information for a specific
language-like entity. The shared `/language/{name}` route remains the
canonical HTML profile route for `language`, `foundation`, and `artifact`
records in the mixed `languages` corpus. Flat `influenced_by` and
`influenced` arrays remain stable for compatibility, and the detail
payload now also includes typed upstream groupings for profile-aware
clients.

- **URL:** `/api/language/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object combining core attributes and profile sections.
  Relevant influence fields include:
  - `influenced_by`: flat upstream names for compatibility.
- `influenced_by_details`: upstream detail records with `name`,
  `display_name`, `entity_type`, and influence `type`.
- `upstream_influence_groups`: grouped upstream records keyed as
  `foundational_precursors`, `language_ancestors`, and, when present,
  `related_artifacts`.

The terminal clients follow the same grouped-lineage contract:

- `atlas influences <name>` renders the grouped upstream sections directly
- `atlas dashboard <name>` uses them in the lineage panel
- the TUI reader and nexus panes use the grouped fields instead of a flat
  upstream list when they are present

### 6. Get Transitive Lineage
Retrieve the full closure-table lineage for a language-like entity.

- **URL:** `/api/lineage/{name}`
- **Method:** `GET`
- **Response:** JSON object containing the root entity, counts, max depths,
  ancestors, and descendants. Ancestors and descendants are sorted by
  `depth ASC, name ASC`.
  ```json
  {
    "name": "Python",
    "display_name": "Python",
    "entity_type": "language",
    "year": 1991,
    "ancestor_count": 5,
    "descendant_count": 12,
    "max_ancestor_depth": 4,
    "max_descendant_depth": 3,
    "ancestors": [
      {
        "name": "C",
        "display_name": "C",
        "entity_type": "language",
        "year": 1972,
        "depth": 2,
        "path_count": 1
      }
    ],
    "descendants": [
      {
        "name": "MicroPython",
        "display_name": "MicroPython",
        "entity_type": "language",
        "year": 2013,
        "depth": 1,
        "path_count": 1
      }
    ]
  }
  ```

### 7. Get Influence Path
Find the shortest known influence path between two language-like entities.

- **URL:** `/api/path`
- **Method:** `GET`
- **Query Params:**
  - `from`: Source language name.
  - `to`: Target language name.
- **Reachable Response:**
  ```json
  {
    "from": "LISP",
    "to": "Clojure",
    "reachable": true,
    "min_depth": 2,
    "path_count": 3,
    "sample_paths": [
      "LISP -> Common Lisp -> Clojure",
      "LISP -> Scheme -> Clojure"
    ]
  }
  ```
- **Not Reachable Response:**
  ```json
  {
    "from": "COBOL",
    "to": "Rust",
    "reachable": false,
    "min_depth": null,
    "path_count": 0,
    "sample_paths": []
  }
  ```

### 8. List Paradigms
Retrieve all programming paradigms known to the system.

- **URL:** `/api/paradigms`
- **Method:** `GET`
- **Response:** Array of strings (paradigm names).

### 9. Get Paradigm Detail
Retrieve detailed information for a specific programming paradigm.

- **URL:** `/api/paradigm/{name}`
- **Method:** `GET`
- **Response:** JSON object with name and description.

### 10. Get Paradigm Ecosystem
Retrieve the foundation-aware ecosystem for a specific paradigm. This keeps the
existing paradigm detail endpoint stable and exposes richer lineage data on a
separate route.

- **URL:** `/api/paradigm/{name}/ecosystem`
- **Method:** `GET`
- **Query Params:**
  - `sort_languages`: `year` (default) or `name`.
- **Response:**
  ```json
  {
    "paradigm": {
      "name": "Functional",
      "description": "..."
    },
    "languages": [
      {
        "name": "Haskell",
        "entity_type": "language",
        "paradigms": ["Functional"]
      }
    ],
    "foundations": [
      {
        "name": "Lambda Calculus",
        "display_name": "Lambda Calculus",
        "year": 1930,
        "philosophy": "...",
        "paradigms": ["Functional"],
        "relevance_score": 130,
        "relevance_reason": "Tagged with Functional and upstream of 3 Functional languages",
        "supporting_language_count": 3,
        "example_languages": ["ML", "Haskell", "F#"],
        "is_directly_tagged": true
      }
    ],
    "stats": {
      "language_count": 3,
      "foundation_count": 1,
      "earliest_language_year": 1973,
      "earliest_foundation_year": 1930
    }
  }
  ```

This is also the conceptual payload surfaced by the CLI via
`atlas paradigm <name>`, which renders the ranked foundations and member
languages in a terminal-friendly layout.

The shared HTML profile route and the API detail route now align on the same
entity-type-aware interpretation of upstream influences:

- foundations surface as `Foundational Precursors`
- languages surface as `Language Ancestors`
- artifacts, when present, surface as `Related Artifacts / Runtime Influences`

### 11. List Concepts
Retrieve all programming concepts and innovations.

- **URL:** `/api/concepts`
- **Method:** `GET`
- **Response:** Array of concept objects.

### 12. Get Concept Detail
Retrieve detailed profile information for a specific programming concept.

- **URL:** `/api/concept/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested concept.

### 13. List Eras
Retrieve summaries of the major historical eras of computing.

- **URL:** `/api/eras`
- **Method:** `GET`
- **Response:** Array of era summary objects.

### 14. Get Era Detail
Retrieve a detailed narrative summary for a specific era.

- **URL:** `/api/era/{slug}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested era.

### 15. List Organizations
Retrieve all organization profiles.

- **URL:** `/api/organizations`
- **Method:** `GET`
- **Response:** Key-value object mapping organization names to their profile data.

### 16. Get Organization Detail
Retrieve detailed information for a specific organization.

- **URL:** `/api/org/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested organization.

### 17. List Odysseys
Retrieve all guided learning paths.

- **URL:** `/api/odysseys`
- **Method:** `GET`
- **Response:** Array of Odyssey objects.

### 18. Get Odyssey Path
Retrieve a specific guided learning path by its ID.

- **URL:** `/api/odyssey/{path_id}`
- **Method:** `GET`
- **Response:** 
  ```json
  {
    "id": "systems_renaissance",
    "title": "The Systems Renaissance",
    "steps": [
      {
        "language": "C",
        "milestone": "The Foundation",
        "challenge": "..."
      }
    ]
  }
  ```

### 19. List People
Retrieve all people profiles.

- **URL:** `/api/people`
- **Method:** `GET`
- **Response:** Key-value object mapping person names to their profile data.

### 20. Get Person Detail
Retrieve detailed profile information for a specific person.

- **URL:** `/api/person/{name}`
- **Method:** `GET`
- **Note:** Names containing spaces may be URL-encoded (`John%20Backus`) or use underscores (`John_Backus`). See "Name Lookup and URL Encoding" below.
- **Response:** Detailed JSON object for the requested person.

### 21. List Historical Events
Retrieve all historical events.

- **URL:** `/api/historical_events`
- **Method:** `GET`
- **Response:** Key-value object mapping event slugs to their event data.

### 22. Get Historical Event Detail
Retrieve detailed information for a specific historical event.

- **URL:** `/api/event/{slug}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested event.

### 23. Reports
Retrieve generated graph-intelligence reports. These endpoints return HTTP
503 if `make derived-data` has not generated the backing JSON file.

- **URL:** `/api/reports/keystones`
- **Method:** `GET`
- **Response:** Contents of `generated-data/reports/keystone-entities.json`.

- **URL:** `/api/reports/bridges`
- **Method:** `GET`
- **Response:** Contents of `generated-data/reports/bridge-entities.json`.

- **URL:** `/api/reports/orphans`
- **Method:** `GET`
- **Response:** Contents of `generated-data/reports/orphan-subgraphs.json`.

### 24. Insights: Paradigm Momentum
Retrieve paradigm momentum data for the insights dashboard.

- **URL:** `/api/insights/momentum`
- **Method:** `GET`
- **Response:** Array of objects with paradigm momentum analytics.

### 25. Visualization Data
Retrieve processed data for timeline and influence visualizations.

- **URL:** `/api/viz/timeline`
- **Method:** `GET`
- **Response:** Array of objects containing language name, year, cluster, and influence score.
- **URL:** `/api/viz/influence`
- **Method:** `GET`
- **Response:** Array of source/target influence relationships.
- **URL:** `/api/viz/influence-expanded`
- **Method:** `GET`
- **Response:** Contents of `generated-data/viz/influence-expanded.json`.
- **Note:** Returns HTTP 503 if `make derived-data` has not generated the
  backing file.

---

## Name Lookup and URL Encoding

All `{name}` path parameters accept either URL-encoded spaces
(`John%20Backus`) or underscores as a substitute for spaces
(`John_Backus`). Both forms work for every name-based endpoint:
`/api/language/{name}`, `/api/person/{name}`, `/api/org/{name}`,
`/api/concept/{name}`.

Slugs (`{slug}` for eras and events) do not use this substitution;
they must match the slug exactly as stored.

## Error Responses

All error responses use standard HTTP status codes.

**404 Not Found** — returned when a named entity does not exist. Note
that 404 responses are rendered as an HTML page (the server's global
exception handler renders `errors/404.html` for all 404s, including
`/api/*` routes). Clients that need to detect a missing entity should
check the HTTP status code, not the response content type.

```
HTTP/1.1 404 Not Found
Content-Type: text/html
```

**Exception:** `GET /api/paradigm/{name}` never returns 404. If the
paradigm is not found, it returns HTTP 200 with a stub object:
```json
{"name": "{requested_name}", "description": "A core model or style of computer programming."}
```

**Other errors** — non-404 HTTP exceptions return JSON:
```json
{"detail": "error message"}
```

The API has no authentication or rate limiting.

## Visualizations
The Web UI provides interactive visualizations at `/visualizations`.

### Python (Requests)
```python
import requests

response = requests.get("http://localhost:8084/api/search", params={"q": "concurrency"})
results = response.json()["results"]
for res in results:
    print(f"[{res['category']}] {res['title']}")
```

### cURL
```bash
curl "http://localhost:8084/api/language/Rust" | jq .
curl "http://localhost:8084/api/historical_events" | jq keys
```
