import sqlite3
import json
import math
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# ─── DATABASE CONNECTION ──────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent.parent / "data" / "search.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

# ═══════════════════════════════════════════════════════════════════════════════
# IN-MEMORY CACHE  (TTL = 2 minutes)
# ═══════════════════════════════════════════════════════════════════════════════

class SimpleCache:
    def __init__(self, ttl_seconds: float = 120):
        self._store: dict[str, dict] = {}
        self.ttl = ttl_seconds

    def get(self, key: str):
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() - entry["ts"] > self.ttl:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value) -> None:
        self._store[key] = {"value": value, "ts": time.monotonic()}

cache = SimpleCache(ttl_seconds=120)

# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="SearchSphere SQLite Service", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def row_to_dict(row):
    d = dict(row)
    if "keywords" in d and isinstance(d["keywords"], str):
        d["keywords"] = d["keywords"].split()
    return d

# ── GET /search ───────────────────────────────────────────────────────────────
@app.get("/search")
def search(
    q:          str            = Query(default=""),
    category:   Optional[str]  = Query(default=None),
    min_price:  Optional[float] = Query(default=None, alias="minPrice"),
    max_price:  Optional[float] = Query(default=None, alias="maxPrice"),
    min_rating: Optional[float] = Query(default=None, alias="minRating"),
    sort:       Optional[str]  = Query(default=None),
):
    cache_key = json.dumps(
        {"q": q, "category": category, "minPrice": min_price,
         "maxPrice": max_price, "minRating": min_rating, "sort": sort},
        sort_keys=True,
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return {"success": True, "count": len(cached), "fromCache": True, "results": cached}

    conn = get_db()
    cursor = conn.cursor()

    # Base query combining products table and FTS5 table
    query_str = """
        SELECT p.*
    """
    
    where_clauses = []
    params = []

    # 1. Full Text Search
    if q and q.strip():
        # FTS5 uses MATCH. We'll use the built-in bm25 ranking.
        query_str += ", bm25(products_fts) AS bm25_score "
        query_str += "FROM products p JOIN products_fts fts ON p.id = fts.rowid "
        
        # Clean query for FTS5 (remove special characters that might break MATCH)
        clean_q = "".join(c for c in q if c.isalnum() or c.isspace()).strip()
        if clean_q:
            # We construct a query like: MATCH 'gaming* OR laptop*' for partial matching
            # Or just use the raw query terms for exact/phrase matches
            fts_query = " OR ".join([f"{word}*" for word in clean_q.split()])
            where_clauses.append("products_fts MATCH ?")
            params.append(fts_query)
    else:
        query_str += "FROM products p "

    # 2. Hard Filters
    if category and category.lower() != "all":
        where_clauses.append("p.category COLLATE NOCASE = ?")
        params.append(category)
        
    if min_price is not None:
        where_clauses.append("p.price >= ?")
        params.append(min_price)
        
    if max_price is not None:
        where_clauses.append("p.price <= ?")
        params.append(max_price)
        
    if min_rating is not None:
        where_clauses.append("p.rating >= ?")
        params.append(min_rating)

    # Combine WHERE
    if where_clauses:
        query_str += " WHERE " + " AND ".join(where_clauses)

    # Execute
    cursor.execute(query_str, params)
    rows = cursor.fetchall()
    
    candidates = [row_to_dict(row) for row in rows]
    
    # 3. Custom Ranking + Sorting
    for p in candidates:
        score = 0.0
        
        # If we have a bm25 score, use it as a base (it's usually negative or low, lower is better in raw bm25)
        # But we'll invert/normalize it and combine it with rating and popularity to mimic our old logic
        bm25 = p.get("bm25_score", 0)
        # In FTS5, bm25() returns lower values for better matches. 
        if "bm25_score" in p:
            # Simple conversion: 
            score += max(0, 30 - (bm25 * 5)) 

        # Add Rating and Popularity modifiers
        score += (p.get("rating", 0) / 5) * 20
        score += (p.get("popularity", 0) / 100) * 10
        
        # Exact Phrase Match Bonus
        if q and q.strip().lower() in p["name"].lower():
            score += 40
            
        p["_score"] = round(score, 1)
        
        # Clean up the row
        if "bm25_score" in p:
            del p["bm25_score"]

    # Sort
    if sort == "price_asc":
        candidates.sort(key=lambda p: p.get("price", 0))
    elif sort == "price_desc":
        candidates.sort(key=lambda p: p.get("price", 0), reverse=True)
    elif sort == "rating":
        candidates.sort(key=lambda p: p.get("rating", 0), reverse=True)
    elif sort == "popularity":
        candidates.sort(key=lambda p: p.get("popularity", 0), reverse=True)
    else:
        # Default: Relevance
        candidates.sort(key=lambda p: p.get("_score", 0), reverse=True)

    conn.close()

    cache.set(cache_key, candidates)
    return {"success": True, "count": len(candidates), "fromCache": False, "results": candidates}

# ── GET /autocomplete ─────────────────────────────────────────────────────────
@app.get("/autocomplete")
def autocomplete(q: str = Query(default="")):
    if not q.strip():
        return {"success": True, "suggestions": []}
        
    clean_q = "".join(c for c in q if c.isalnum() or c.isspace()).strip()
    if not clean_q:
        return {"success": True, "suggestions": []}

    conn = get_db()
    cursor = conn.cursor()
    
    # Use FTS5 prefix matching
    # E.g., MATCH 'wire*' against the name column
    fts_query = f"^{clean_q}*" 
    
    cursor.execute("""
        SELECT p.name 
        FROM products p 
        JOIN products_fts fts ON p.id = fts.rowid
        WHERE products_fts MATCH ?
        LIMIT 8
    """, (fts_query,))
    
    rows = cursor.fetchall()
    suggestions = [row["name"] for row in rows]
    conn.close()
    
    return {"success": True, "suggestions": suggestions}

# ── GET /recommendations/{id} ─────────────────────────────────────────────────
@app.get("/recommendations/{product_id}")
def recommendations(product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get base product
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    base_row = cursor.fetchone()
    
    if not base_row:
        conn.close()
        return {"success": False, "recommendations": []}
        
    base_product = row_to_dict(base_row)
    
    # Find similar products based on category and price proximity
    min_p = base_product["price"] * 0.5
    max_p = base_product["price"] * 1.5
    cat = base_product["category"]
    
    cursor.execute("""
        SELECT * FROM products 
        WHERE id != ? AND category = ? AND price BETWEEN ? AND ?
        LIMIT 6
    """, (product_id, cat, min_p, max_p))
    
    rows = cursor.fetchall()
    recs = [row_to_dict(row) for row in rows]
    conn.close()

    return {"success": True, "recommendations": recs}

# ── GET /categories ───────────────────────────────────────────────────────────
@app.get("/categories")
def categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
    rows = cursor.fetchall()
    cats = [row["category"] for row in rows if row["category"]]
    conn.close()
    
    return {"success": True, "categories": cats}

# ── GET /health ───────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM products")
    count = cursor.fetchone()["c"]
    conn.close()
    
    return {"status": "ok", "products": count, "engine": "sqlite-fts5"}

# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=False)
