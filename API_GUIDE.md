# Language Atlas API Reference

The Language Atlas provides a RESTful API for programmatic access to programming language history, influences, and guided learning paths (Odysseys).

## Base URL
The API is exposed via the FastAPI web interface (default: `http://localhost:8084/api`).

---

## Endpoints

### 1. Semantic Search
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

### 2. List Languages
Retrieve a list of all languages with optional filtering and sorting.

- **URL:** `/api/languages`
- **Method:** `GET`
- **Query Params:** 
  - `cluster`: Filter by functional domain. Options: `AI`, `academic`, `backend`, `business`, `cloud`, `data`, `education`, `enterprise`, `finance`, `frontend`, `historical`, `infra`, `mathematics`, `safety-critical`, `scientific`, `scripting`, `systems`, `web`.
  - `generation`: Filter by era/generation. Options: `dawn`, `early`, `web1`, `cloud`, `renaissance`, `autonomic`.
  - `sort`: `year` (default) or `name`.
  - `min_year`: Integer (default: 1930).
  - `max_year`: Integer (default: 2024).
- **Response:** Array of language objects.

### 3. Get Language Detail
Retrieve core data and extended profile information for a specific language.

- **URL:** `/api/language/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object combining core attributes and profile sections.

### 4. List Paradigms
Retrieve all programming paradigms known to the system.

- **URL:** `/api/paradigms`
- **Method:** `GET`
- **Response:** Array of strings (paradigm names).

### 5. Get Paradigm Detail
Retrieve detailed information for a specific programming paradigm.

- **URL:** `/api/paradigm/{name}`
- **Method:** `GET`
- **Response:** JSON object with name and description.

### 6. List Concepts
Retrieve all programming concepts and innovations.

- **URL:** `/api/concepts`
- **Method:** `GET`
- **Response:** Array of concept objects.

### 7. Get Concept Detail
Retrieve detailed profile information for a specific programming concept.

- **URL:** `/api/concept/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested concept.

### 8. List Eras
Retrieve summaries of the major historical eras of computing.

- **URL:** `/api/eras`
- **Method:** `GET`
- **Response:** Array of era summary objects.

### 9. Get Era Detail
Retrieve a detailed narrative summary for a specific era.

- **URL:** `/api/era/{slug}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested era.

### 10. List Organizations
Retrieve all organization profiles.

- **URL:** `/api/organizations`
- **Method:** `GET`
- **Response:** Key-value object mapping organization names to their profile data.

### 11. Get Organization Detail
Retrieve detailed information for a specific organization.

- **URL:** `/api/org/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested organization.

### 12. List Odysseys
Retrieve all guided learning paths.

- **URL:** `/api/odysseys`
- **Method:** `GET`
- **Response:** Array of Odyssey objects.

### 13. Get Odyssey Path
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

### 14. List People
Retrieve all people profiles.

- **URL:** `/api/people`
- **Method:** `GET`
- **Response:** Key-value object mapping person names to their profile data.

### 15. Get Person Detail
Retrieve detailed profile information for a specific person.

- **URL:** `/api/person/{name}`
- **Method:** `GET`
- **Note:** Names containing spaces must be URL-encoded (e.g., `/api/person/John%20Backus`). The API also accepts underscores as a substitute for spaces (e.g., `/api/person/John_Backus`).
- **Response:** Detailed JSON object for the requested person.

### 16. List Historical Events
Retrieve all historical events.

- **URL:** `/api/historical_events`
- **Method:** `GET`
- **Response:** Key-value object mapping event slugs to their event data.

### 17. Get Historical Event Detail
Retrieve detailed information for a specific historical event.

- **URL:** `/api/event/{slug}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested event.

### 18. Insights: Paradigm Momentum
Retrieve paradigm momentum data for the insights dashboard.

- **URL:** `/api/insights/momentum`
- **Method:** `GET`
- **Response:** Array of objects with paradigm momentum analytics.

### 19. Visualization Data
Retrieve processed data for timeline and influence visualizations.

- **URL:** `/api/viz/timeline`
- **Method:** `GET`
- **Response:** Array of objects containing language name, year, cluster, and influence score.
- **URL:** `/api/viz/influence`
- **Method:** `GET`
- **Response:** Array of source/target influence relationships.

---

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
