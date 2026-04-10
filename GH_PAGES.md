# GitHub Pages Deployment

This document describes how to build and deploy the Language Atlas
static export to GitHub Pages.

## Why a hand-maintained branch

The project uses a manually maintained `gh-pages` branch rather than a
GitHub Actions workflow. This choice keeps the build toolchain entirely
local, avoids storing secrets in CI, and gives the maintainer full
control over what ends up on the published site. The trade-off is that
deployment is a manual step after each significant change to `main`.

## One-time setup

Run these commands once to create the `gh-pages` branch:

```bash
git checkout --orphan gh-pages
git rm -rf .
git commit --allow-empty -m "[gh-pages] Initial empty branch"
git push origin gh-pages
```

Then, in the GitHub repository settings, configure GitHub Pages to serve
from the `gh-pages` branch at the root (`/`).

## Recurring deploy

After merging changes into `main`, update the published site:

```bash
git checkout gh-pages
git merge main --no-ff
make pages
git add site language_atlas.sqlite .nojekyll index.html
git commit -m "[gh-pages] Refresh from main @ <sha>"
git push origin gh-pages
git checkout main
```

Replace `<sha>` with the short commit hash from `main` (for example,
`git rev-parse --short main`). The `make pages` script prints the
suggested commit message automatically.

## What `make pages` does

The `pages` target runs three steps in sequence:

1. `make build` - rebuilds `language_atlas.sqlite` from the JSON sources
   in `data/`.
2. `make site` - runs `SiteCrawler` via `TestClient` to write a
   fully-rendered static HTML mirror of the live FastAPI app into
   `site/`.
3. `uv run python scripts/prep_pages.py` - copies the database to
   `site/db/atlas/db.sqlite3`, writes `site/db/atlas/config.json` for
   `sql.js-httpvfs`, writes `.nojekyll` at the repo root, and writes the
   root redirect `index.html`.

`prep_pages.py` will refuse to run on the `main` branch with the message
"Refusing to build pages artifacts on main; switch to gh-pages first."

## How the client-side SQLite layer works

The static site bundles the SQLite database under `site/db/atlas/` and
loads it in the browser using
[phiresky/sql.js-httpvfs](https://github.com/phiresky/sql.js-httpvfs),
the technique described in the blog post
[Hosting SQLite databases on Github Pages](https://phiresky.github.io/blog/2021/hosting-sqlite-databases-on-github-pages/).

The library uses HTTP range requests to fetch only the 4 KiB SQLite
pages required to satisfy each query, rather than downloading the entire
database up front. GitHub Pages supports range requests, so this keeps
initial page loads fast even for multi-megabyte databases.

The JavaScript shim lives at `src/app/static/atlas-static.js`. It is
loaded as an ES module only when `ATLAS_STATIC_MODE=1` is set (the
flag that `SiteCrawler` injects during the crawl). On boot, the shim:

1. Instantiates a `createDbWorker` pointing at `db/atlas/config.json`.
2. Removes the static-mode notice from the page if the worker starts
   successfully.
3. Hooks the filter form so cluster, paradigm, and year changes trigger
   live SQL queries against `languages` and `language_paradigms`.
4. Hooks the search box (debounced 200ms) to query the FTS5
   `search_index` virtual table and render results inline.

If the worker fails to initialize, the static-mode notice remains
visible and the page continues to display the pre-rendered content.

## Local preview before pushing

Serve the repo root with Python's built-in HTTP server:

```bash
cd <repo-root>
uv run python -m http.server 8085
open http://localhost:8085/
```

The root `index.html` redirects to `site/`, which is the static export.
The `sql.js-httpvfs` worker will load the database from
`http://localhost:8085/site/db/atlas/db.sqlite3`.

Note: range requests work correctly with Python's HTTP server from
Python 3.9 onwards.

## Gitignore override on the gh-pages branch

The following paths are gitignored on `main` to keep the development
branch clean:

```
site/
/index.html
.nojekyll
language_atlas.sqlite (via *.sqlite)
```

On the `gh-pages` branch these files must be committed. There are two
options:

**Option 1: force-add** (simplest, no extra files required)

```bash
git add -f site language_atlas.sqlite .nojekyll index.html
```

**Option 2: branch-specific .gitignore** (cleaner for repeated deploys)

On the `gh-pages` branch only, replace `.gitignore` with a version that
does not ignore those paths. Keep `site/` and `*.sqlite` in the `main`
`.gitignore` and manage the `gh-pages` version separately. Because
`.gitignore` itself is tracked, the branch-specific version will not
bleed back to `main` as long as you do not merge it.

The `make pages` step prints a reminder with the exact `git add` command
to use after it completes.

## Troubleshooting

**Worker fails to initialize (console shows a fetch error)**

- Check that `site/db/atlas/db.sqlite3` and
  `site/db/atlas/config.json` are present on the `gh-pages` branch.
- Verify the `config.json` `databaseLengthBytes` field matches the
  actual file size of `db.sqlite3`.
- Confirm the CDN URLs for `sqlite.worker.js` and `sql-wasm.wasm` in
  `atlas-static.js` are reachable from the browser.

**Worker boots but queries return no results**

- Check the browser console for SQL errors (logged with the
  `[atlas-static]` prefix).
- Verify `language_atlas.sqlite` was built from current JSON sources
  (`make build`) before running `make pages`.

**Static-mode notice never disappears**

- The notice is removed by `atlas-static.js` on successful boot. If it
  persists after the page has fully loaded, open the browser console and
  look for `[atlas-static]` error messages.
- If `atlas-static.js` itself fails to load, check that
  `site/static/atlas-static.js` exists in the deployed tree.

**Validating the database layout**

```bash
ls -lh site/db/atlas/
cat site/db/atlas/config.json
```

The directory should contain `db.sqlite3` and `config.json`. The
`databaseLengthBytes` in the config should equal the size of
`db.sqlite3`.
