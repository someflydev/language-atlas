// atlas-static.js — client-side SQLite shim for the static export.
//
// Loads sql.js-httpvfs from CDN and progressively enhances the page:
//   - Hooks the filter form to run live SQL queries on change.
//   - Hooks the search box (debounced 200ms) to query the FTS5 index.
//   - Removes the static-mode notice once the worker boots successfully.
//   - Leaves the notice in place if the worker fails so the page still
//     shows useful content.
//
// This script is intentionally small (under 200 lines). It is not a SPA;
// it enhances the already-rendered static HTML in place.

// esm.sh is used instead of the jsDelivr dist/index.js URL because
// dist/index.js is a UMD bundle; browsers cannot import named exports
// from it via <script type="module">. esm.sh wraps the package as a
// proper ES module and re-exports its named bindings correctly.
import { createDbWorker } from "https://esm.sh/sql.js-httpvfs@0.8.12";

// Worker JS and WASM are still loaded directly from jsDelivr because
// they are passed as URL strings to createDbWorker (not imported as
// ES modules) and jsDelivr reliably serves them with correct MIME types.
const WORKER_URL =
  "https://cdn.jsdelivr.net/npm/sql.js-httpvfs@0.8.12/dist/sqlite.worker.js";
const WASM_URL =
  "https://cdn.jsdelivr.net/npm/sql.js-httpvfs@0.8.12/dist/sql-wasm.wasm";

// This script is always at <site-root>/static/atlas-static.js, so
// the db config is one directory up and then into db/atlas/.
const CONFIG_URL = new URL("../db/atlas/config.json", import.meta.url).href;
const SITE_ROOT = new URL("../", import.meta.url).href;

// ---------------------------------------------------------------------------
// SQL helpers
// ---------------------------------------------------------------------------

async function queryLanguages(worker, { clusters, paradigms, minYear, maxYear, sort }) {
  const conditions = [];
  const params = [];

  if (minYear != null) { conditions.push("l.year >= ?"); params.push(minYear); }
  if (maxYear != null) { conditions.push("l.year <= ?"); params.push(maxYear); }
  if (clusters.length) {
    conditions.push(`l.cluster IN (${clusters.map(() => "?").join(",")})`);
    params.push(...clusters);
  }
  if (paradigms.length) {
    const ph = paradigms.map(() => "?").join(",");
    conditions.push(
      `l.id IN (SELECT lp2.language_id FROM language_paradigms lp2 ` +
      `JOIN paradigms p2 ON lp2.paradigm_id = p2.id WHERE p2.name IN (${ph}))`
    );
    params.push(...paradigms);
  }

  const where = conditions.length ? "WHERE " + conditions.join(" AND ") : "";
  const orderBy = sort === "year" ? "l.year ASC, l.name ASC" : "l.name ASC";
  const sql = `
    SELECT l.name, l.display_name, l.year, l.cluster, l.philosophy,
      (SELECT p.name FROM language_paradigms lp
       JOIN paradigms p ON lp.paradigm_id = p.id
       WHERE lp.language_id = l.id ORDER BY lp.order_index ASC LIMIT 1) AS first_paradigm
    FROM languages l ${where} ORDER BY ${orderBy}`;

  return await worker.db.query(sql, params);
}

async function querySearch(worker, query) {
  return await worker.db.query(
    `SELECT entity_type, entity_id, title,
       snippet(search_index, 3, '<mark>', '</mark>', '...', 24) AS snippet,
       entity_id AS link_name
     FROM search_index WHERE search_index MATCH ?
     ORDER BY rank LIMIT 20`,
    [query + "*"]
  );
}

// ---------------------------------------------------------------------------
// DOM rendering helpers
// ---------------------------------------------------------------------------

function esc(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function renderCard(lang) {
  const langUrl = SITE_ROOT + "language/" + encodeURIComponent(lang.name) + "/";
  const clusterUrl = SITE_ROOT + "cluster/" + encodeURIComponent(lang.cluster || "") + "/";
  const paradigmUrl = SITE_ROOT + "paradigm/" + encodeURIComponent(lang.first_paradigm || "") + "/";
  const paradigmTag = lang.first_paradigm
    ? `<a href="${paradigmUrl}" class="text-[10px] font-black uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-1 rounded hover:bg-blue-100 transition-colors">${esc(lang.first_paradigm)}</a>`
    : "";
  return `<div class="card-container group relative flex flex-col h-full">
    <article class="card h-full flex flex-col p-6 bg-white rounded-2xl border border-slate-100 shadow-sm transition-all duration-300 group-hover:shadow-xl group-hover:border-blue-100 group-hover:-translate-y-1 relative">
      <header class="mb-4">
        <div class="flex justify-between items-start mb-3">
          <h2 class="text-xl font-black text-slate-900 group-hover:text-blue-600 transition-colors">${esc(lang.display_name)}</h2>
          <span class="text-xs font-bold text-slate-400">${esc(lang.year)}</span>
        </div>
        <div class="flex flex-wrap gap-2 relative z-30">
          ${paradigmTag}
          <a href="${clusterUrl}" class="text-[10px] font-black uppercase tracking-wider text-slate-400 border border-slate-100 px-2 py-1 rounded hover:bg-slate-50 transition-colors">${esc(lang.cluster)}</a>
        </div>
      </header>
      <p class="text-sm text-slate-500 leading-relaxed line-clamp-3 italic mb-4">"${esc(lang.philosophy)}"</p>
      <div class="mt-auto pt-4 flex justify-between items-center relative z-30">
        <a href="${langUrl}" class="text-xs font-bold uppercase text-blue-600 hover:text-blue-800 transition-colors">View Profile &rarr;</a>
      </div>
      <a href="${langUrl}" class="absolute inset-0 z-10 rounded-2xl cursor-pointer" aria-label="View ${esc(lang.display_name)} profile"></a>
    </article>
  </div>`;
}

function renderSearchResults(rows, query) {
  if (!rows.length) {
    return `<div class="absolute top-full left-0 right-0 z-50 mt-2 bg-white rounded-xl shadow-2xl border border-slate-200 p-8 text-center">
      <p class="text-sm font-bold text-slate-400">No matches found for "${esc(query)}"</p></div>`;
  }
  const items = rows.map(r => {
    const cat = r.entity_type || "language";
    const routeMap = { era: "narrative/era", concept: "concept", person: "person", paradigm: "paradigm" };
    const route = routeMap[cat] || "language";
    const href = SITE_ROOT + route + "/" + encodeURIComponent((r.link_name || "").replace(/ /g, "_")) + "/";
    const badge = cat === "language" ? "bg-blue-50 text-blue-600" : "bg-amber-50 text-amber-600";
    return `<a href="${href}" class="block p-4 hover:bg-slate-50 rounded-lg transition-colors border-b border-slate-50 last:border-0 group">
      <div class="flex justify-between items-start mb-1">
        <span class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">${esc(r.title)}</span>
        <span class="text-[10px] font-black uppercase px-2 py-0.5 rounded ${badge}">${esc(cat)}</span>
      </div>
      <p class="text-xs text-slate-500 line-clamp-2 leading-relaxed">...${r.snippet || ""}...</p></a>`;
  }).join("");
  return `<div class="absolute top-full left-0 right-0 z-50 mt-2 bg-white rounded-xl shadow-2xl border border-slate-200 max-h-[70vh] overflow-y-auto overflow-x-hidden p-2">
    <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 px-4 py-2">Search Results (${rows.length})</div>
    ${items}</div>`;
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", async () => {
  const notice = document.getElementById("static-mode-notice");

  try {
    const worker = await createDbWorker(
      [{ from: "jsonconfig", configUrl: CONFIG_URL }],
      WORKER_URL,
      WASM_URL,
    );

    // Worker booted: remove the static notice.
    if (notice) notice.remove();

    // Wire filter form.
    const grid = document.getElementById("language-grid");
    if (grid) {
      const filterForm = document.querySelector("form[hx-get]");
      if (filterForm) {
        filterForm.addEventListener("change", async () => {
          const clusters = [...document.querySelectorAll('input[name="clusters"]:checked')].map(el => el.value);
          const paradigms = [...document.querySelectorAll('input[name="paradigms"]:checked')].map(el => el.value);
          const minYear = parseInt(document.getElementById("min_year")?.value) || null;
          const maxYear = parseInt(document.getElementById("max_year")?.value) || null;
          const sort = document.querySelector('input[name="sort"]:checked')?.value || "name";
          try {
            const rows = await queryLanguages(worker, { clusters, paradigms, minYear, maxYear, sort });
            grid.innerHTML = rows.map(renderCard).join("");
          } catch (e) { console.error("[atlas-static] filter error:", e); }
        });
      }
    }

    // Wire search box (debounced 200ms).
    const searchInput = document.querySelector('input[name="q"]');
    const searchResults = document.getElementById("search-results");
    if (searchInput && searchResults) {
      // Disconnect HTMX so the static worker handles search instead.
      ["hx-get", "hx-trigger", "hx-target", "hx-swap", "hx-indicator"].forEach(
        attr => searchInput.removeAttribute(attr)
      );
      let timer = null;
      searchInput.addEventListener("input", () => {
        clearTimeout(timer);
        timer = setTimeout(async () => {
          const q = searchInput.value.trim();
          if (q.length < 2) { searchResults.innerHTML = ""; return; }
          try {
            const rows = await querySearch(worker, q);
            searchResults.innerHTML = renderSearchResults(rows, q);
          } catch (e) {
            console.error("[atlas-static] search error:", e);
            searchResults.innerHTML = "";
          }
        }, 200);
      });
    }
  } catch (err) {
    console.error("[atlas-static] worker failed to initialize:", err);
    // Leave the static-mode notice visible so the page stays informative.
  }
});
