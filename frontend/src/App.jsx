import { useState, useEffect } from "react";
import SearchBar from "./components/SearchBar";
import Filters from "./components/Filters";
import ProductCard from "./components/ProductCard";
import Recommendations from "./components/Recommendations";

const API = "http://localhost:5000";
const DEFAULT_FILTERS = { category: "All", minPrice: "", maxPrice: "", minRating: "" };

const SORT_OPTIONS = [
  { value: "relevance", label: "Relevance" },
  { value: "price_asc",  label: "Price ↑" },
  { value: "price_desc", label: "Price ↓" },
  { value: "rating",     label: "Top Rated" },
  { value: "popularity", label: "Popular" },
];

function hasActiveFilters(f) {
  return f.category !== "All" || f.minPrice !== "" || f.maxPrice !== "" || f.minRating !== "";
}

export default function App() {
  const [query,           setQuery]           = useState("");
  const [results,         setResults]         = useState([]);
  const [loading,         setLoading]         = useState(false);
  const [error,           setError]           = useState(null);
  const [fromCache,       setFromCache]       = useState(false);
  const [hasSearched,     setHasSearched]     = useState(false);
  const [filters,         setFilters]         = useState(DEFAULT_FILTERS);
  const [sort,            setSort]            = useState("relevance");
  const [categories,      setCategories]      = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [filtersOpen,     setFiltersOpen]     = useState(false);

  // Load categories once
  useEffect(() => {
    fetch(`${API}/api/categories`)
      .then((r) => r.json())
      .then((d) => setCategories(d.categories || []))
      .catch(() => {});
  }, []);

  // Re-search on filter/sort change if a search has been made
  useEffect(() => {
    if (hasSearched) doSearch(query, filters, sort);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, sort]);

  // Close drawer on Escape key
  useEffect(() => {
    function onKey(e) { if (e.key === "Escape") setFiltersOpen(false); }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  async function doSearch(q, f = filters, s = sort) {
    setLoading(true);
    setError(null);
    setSelectedProduct(null);

    const params = new URLSearchParams();
    if (q)                                params.set("q",         q);
    if (f.category && f.category !== "All") params.set("category",  f.category);
    if (f.minPrice  !== "")               params.set("minPrice",  f.minPrice);
    if (f.maxPrice  !== "")               params.set("maxPrice",  f.maxPrice);
    if (f.minRating !== "")               params.set("minRating", f.minRating);
    if (s && s !== "relevance")           params.set("sort",      s);

    try {
      const res  = await fetch(`${API}/api/search?${params}`);
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "Search failed");
      setResults(data.results);
      setFromCache(data.fromCache);
      setHasSearched(true);
    } catch {
      setError("Could not reach the search server. Is the backend running on port 5000?");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(q) {
    setQuery(q);
    doSearch(q, filters, sort);
  }

  return (
    <div className="app-container">

      {/* ── HEADER ─────────────────────────────────── */}
      <header className="header">
        <a href="/" className="logo">
          <img src="/search.jpg" alt="SearchSphere" className="logo-icon" />
          <div>
            <div className="logo-text">SearchSphere</div>
            <div className="header-tagline">Product Search Engine</div>
          </div>
        </a>
        <div className="header-right">
          {fromCache && results.length > 0 && (
            <div className="cache-badge">⚡ cached</div>
          )}
        </div>
      </header>

      {/* ── HERO / SEARCH ──────────────────────────── */}
      <section className="search-hero">
        <h1 className="hero-title">Find Anything, Instantly</h1>
        <p className="hero-sub">Ranked by relevance · Inverted Index + Trie autocomplete</p>
        <SearchBar onSearch={handleSearch} />
      </section>

      {/* ── TOOLBAR (filter button + sort + count) ─── */}
      <div className="results-toolbar">
        <div className="toolbar-left">
          {/* Filter toggle button */}
          <button
            id="filter-toggle-btn"
            className={`filter-toggle-btn ${filtersOpen ? "active" : ""}`}
            onClick={() => setFiltersOpen((v) => !v)}
          >
            {hasActiveFilters(filters) && <span className="filter-dot" />}
            ☰ Filters
          </button>

          {/* Result count */}
          {hasSearched && !loading && (
            <p className="results-count">
              {results.length > 0 ? (
                <>
                  <strong>{results.length}</strong> result{results.length !== 1 ? "s" : ""}
                  {query && <> for "<strong>{query}</strong>"</>}
                </>
              ) : (
                <>No results {query && <>for "<strong>{query}</strong>"</>}</>
              )}
            </p>
          )}
        </div>

        {/* Sort buttons */}
        <div className="toolbar-right">
          <span className="sort-label">Sort:</span>
          {SORT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              className={`sort-btn ${sort === opt.value ? "active" : ""}`}
              onClick={() => setSort(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── FILTERS DRAWER ─────────────────────────── */}
      {filtersOpen && (
        <Filters
          categories={categories}
          filters={filters}
          onFilterChange={setFilters}
          onClose={() => setFiltersOpen(false)}
        />
      )}

      {/* ── MAIN CONTENT ───────────────────────────── */}
      <div className="main-content">

        {/* Error */}
        {error && (
          <div className="state-container">
            <span className="state-icon">⚠️</span>
            <p className="state-title">Backend not reachable</p>
            <p className="state-sub">{error}</p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="loader">
            <div className="spinner" />
            <span>Searching…</span>
          </div>
        )}

        {/* Welcome state */}
        {!hasSearched && !loading && !error && (
          <div className="state-container">
            <span className="state-icon">🛍️</span>
            <p className="state-title">Start searching to discover products</p>
            <p className="state-sub">Try "wireless headphones", "gaming laptop", or "running shoes"</p>
          </div>
        )}

        {/* Products grid */}
        {!loading && !error && results.length > 0 && (
          <div className="products-grid">
            {results.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onSelect={setSelectedProduct}
              />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && hasSearched && results.length === 0 && (
          <div className="state-container">
            <span className="state-icon">🔍</span>
            <p className="state-title">No products found</p>
            <p className="state-sub">Try different keywords or loosen your filters</p>
          </div>
        )}

        {/* Recommendations */}
        {selectedProduct && (
          <Recommendations
            productId={selectedProduct.id}
            onSelect={setSelectedProduct}
          />
        )}
      </div>
    </div>
  );
}
