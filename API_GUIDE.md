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
      "/api/language/{name}": "Detailed language profile data"
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
Retrieve core data and extended profile information for a specific language.

- **URL:** `/api/language/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object combining core attributes and profile sections.

### 6. List Paradigms
Retrieve all programming paradigms known to the system.

- **URL:** `/api/paradigms`
- **Method:** `GET`
- **Response:** Array of strings (paradigm names).

### 7. Get Paradigm Detail
Retrieve detailed information for a specific programming paradigm.

- **URL:** `/api/paradigm/{name}`
- **Method:** `GET`
- **Response:** JSON object with name and description.

### 8. Get Paradigm Ecosystem
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

### 9. List Concepts
Retrieve all programming concepts and innovations.

- **URL:** `/api/concepts`
- **Method:** `GET`
- **Response:** Array of concept objects.

### 10. Get Concept Detail
Retrieve detailed profile information for a specific programming concept.

- **URL:** `/api/concept/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested concept.

### 11. List Eras
Retrieve summaries of the major historical eras of computing.

- **URL:** `/api/eras`
- **Method:** `GET`
- **Response:** Array of era summary objects.

### 12. Get Era Detail
Retrieve a detailed narrative summary for a specific era.

- **URL:** `/api/era/{slug}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested era.

### 13. List Organizations
Retrieve all organization profiles.

- **URL:** `/api/organizations`
- **Method:** `GET`
- **Response:** Key-value object mapping organization names to their profile data.

### 14. Get Organization Detail
Retrieve detailed information for a specific organization.

- **URL:** `/api/org/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested organization.

### 15. List Odysseys
Retrieve all guided learning paths.

- **URL:** `/api/odysseys`
- **Method:** `GET`
- **Response:** Array of Odyssey objects.

### 16. Get Odyssey Path
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

### 17. List People
Retrieve all people profiles.

- **URL:** `/api/people`
- **Method:** `GET`
- **Response:** Key-value object mapping person names to their profile data.

### 18. Get Person Detail
Retrieve detailed profile information for a specific person.

- **URL:** `/api/person/{name}`
- **Method:** `GET`
- **Note:** Names containing spaces may be URL-encoded (`John%20Backus`) or use underscores (`John_Backus`). See "Name Lookup and URL Encoding" below.
- **Response:** Detailed JSON object for the requested person.

### 19. List Historical Events
Retrieve all historical events.

- **URL:** `/api/historical_events`
- **Method:** `GET`
- **Response:** Key-value object mapping event slugs to their event data.

### 20. Get Historical Event Detail
Retrieve detailed information for a specific historical event.

- **URL:** `/api/event/{slug}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested event.

### 21. Insights: Paradigm Momentum
Retrieve paradigm momentum data for the insights dashboard.

- **URL:** `/api/insights/momentum`
- **Method:** `GET`
- **Response:** Array of objects with paradigm momentum analytics.

### 22. Visualization Data
Retrieve processed data for timeline and influence visualizations.

- **URL:** `/api/viz/timeline`
- **Method:** `GET`
- **Response:** Array of objects containing language name, year, cluster, and influence score.
- **URL:** `/api/viz/influence`
- **Method:** `GET`
- **Response:** Array of source/target influence relationships.

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
