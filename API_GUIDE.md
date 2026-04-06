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
Retrieve a list of all languages with optional filtering.

- **URL:** `/api/languages`
- **Method:** `GET`
- **Query Params:** 
  - `cluster` (e.g., `systems`, `web`)
  - `generation` (e.g., `renaissance`, `cloud`)
- **Response:** Array of language objects.

### 3. Get Language Detail
Retrieve core data and extended profile information for a specific language.

- **URL:** `/api/language/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object combining core attributes and profile sections.

### 4. List Odysseys
Retrieve all guided learning paths.

- **URL:** `/api/odysseys`
- **Method:** `GET`
- **Response:** Array of Odyssey objects.

### 5. Get Odyssey Path
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

### 6. List People
Retrieve all people profiles.

- **URL:** `/api/people`
- **Method:** `GET`
- **Response:** Key-value object mapping person names to their profile data.

### 7. Get Person Detail
Retrieve detailed profile information for a specific person.

- **URL:** `/api/person/{name}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested person.

### 8. List Historical Events
Retrieve all historical events.

- **URL:** `/api/events`
- **Method:** `GET`
- **Response:** Key-value object mapping event slugs to their event data.

### 9. Get Historical Event Detail
Retrieve detailed information for a specific historical event.

- **URL:** `/api/event/{slug}`
- **Method:** `GET`
- **Response:** Detailed JSON object for the requested event.

### 10. Visualization Data
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
```
