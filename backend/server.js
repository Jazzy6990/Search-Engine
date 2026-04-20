const express = require("express");
const cors    = require("cors");

const app    = express();
const PORT   = process.env.PORT   || 5000;
const PYTHON = process.env.PYTHON_URL || "http://localhost:5001";

// ─── Middleware ───────────────────────────────────────────────────────────────
app.use(cors());
app.use(express.json());

// ─── Helper: forward a request to the Python search service ──────────────────
async function pyFetch(path) {
  // Node 18+ ships with native fetch; fall back to dynamic import for older versions
  const fetcher = typeof fetch !== "undefined" ? fetch : (await import("node-fetch")).default;
  const res  = await fetcher(`${PYTHON}${path}`);
  if (!res.ok) throw new Error(`Python service error: ${res.status}`);
  return res.json();
}

// ─── Routes ───────────────────────────────────────────────────────────────────

// GET /api/search?q=&category=&minPrice=&maxPrice=&minRating=&sort=
app.get("/api/search", async (req, res) => {
  try {
    // Forward all query params unchanged to the Python service
    const qs   = new URLSearchParams(req.query).toString();
    const data = await pyFetch(`/search?${qs}`);
    res.json({ ...data, query: req.query.q || "" });
  } catch (err) {
    console.error("[/api/search]", err.message);
    res.status(502).json({ success: false, error: "Search service unavailable" });
  }
});

// GET /api/autocomplete?q=
app.get("/api/autocomplete", async (req, res) => {
  try {
    const qs   = new URLSearchParams(req.query).toString();
    const data = await pyFetch(`/autocomplete?${qs}`);
    res.json(data);
  } catch (err) {
    console.error("[/api/autocomplete]", err.message);
    res.status(502).json({ success: false, error: "Autocomplete unavailable" });
  }
});

// GET /api/recommendations/:id
app.get("/api/recommendations/:id", async (req, res) => {
  try {
    const data = await pyFetch(`/recommendations/${req.params.id}`);
    res.json(data);
  } catch (err) {
    console.error("[/api/recommendations]", err.message);
    res.status(502).json({ success: false, error: "Recommendations unavailable" });
  }
});

// GET /api/categories
app.get("/api/categories", async (req, res) => {
  try {
    const data = await pyFetch("/categories");
    res.json(data);
  } catch (err) {
    console.error("[/api/categories]", err.message);
    res.status(502).json({ success: false, error: "Categories unavailable" });
  }
});

// GET /api/health  — includes Python service health
app.get("/api/health", async (req, res) => {
  let pyHealth = null;
  try { pyHealth = await pyFetch("/health"); } catch { /* ignore */ }
  res.json({ status: "ok", express: true, python: pyHealth });
});

// ─── Start ────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n🚀 Express gateway running on  http://localhost:${PORT}`);
  console.log(`   Proxying search logic to     ${PYTHON}`);
  console.log(`\n   Endpoints:`);
  console.log(`   • GET /api/search?q=<query>&category=&minPrice=&maxPrice=&minRating=&sort=`);
  console.log(`   • GET /api/autocomplete?q=<prefix>`);
  console.log(`   • GET /api/recommendations/:id`);
  console.log(`   • GET /api/categories`);
  console.log(`   • GET /api/health\n`);
});
