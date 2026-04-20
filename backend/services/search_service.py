import json
import math
import re
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# ─── LOAD PRODUCTS ────────────────────────────────────────────────────────────

DATA_PATH = Path(__file__).parent.parent / "data" / "products.json"
with open(DATA_PATH, encoding="utf-8") as f:
    PRODUCTS: list[dict] = json.load(f)


# TRIE

class TrieNode:
    __slots__ = ("children", "is_end", "suggestions")

    def __init__(self):
        self.children: dict[str, "TrieNode"] = {}
        self.is_end: bool = False
        self.suggestions: list[str] = []   # up to 8 suggestions stored per node


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word.lower():
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
            if word not in node.suggestions and len(node.suggestions) < 8:
                node.suggestions.append(word)
        node.is_end = True

    def get_suggestions(self, prefix: str) -> list[str]:
        node = self.root
        for ch in prefix.lower():
            if ch not in node.children:
                return []
            node = node.children[ch]
        return node.suggestions


# INVERTED INDEX

class InvertedIndex:
    def __init__(self):
        self.index: dict[str, set[int]] = {}   # token -> set of product IDs

    def add(self, product_id: int, keywords: list[str]) -> None:
        for kw in keywords:
            for word in re.split(r"\s+", kw.lower()):
                if word:
                    self.index.setdefault(word, set()).add(product_id)

    def _match_word(self, word: str) -> set[int]:
        """Prefix + substring matching for a single token."""
        result: set[int] = set()
        for indexed_word, ids in self.index.items():
            if indexed_word.startswith(word) or word in indexed_word:
                result.update(ids)
        return result

    def search(self, query: str) -> set[int]:
        """AND search with OR fallback."""
        words = [w for w in re.split(r"\s+", query.lower()) if len(w) > 1]
        if not words:
            return set()

        # AND search — intersect
        result: Optional[set[int]] = None
        for word in words:
            matches = self._match_word(word)
            result = matches if result is None else result & matches

        # Fallback to OR if AND gives nothing
        if not result:
            result = set()
            for word in words:
                result.update(self._match_word(word))

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# RANKING
# ═══════════════════════════════════════════════════════════════════════════════

def rank_products(products: list[dict], query: str) -> list[dict]:
    query_words = [w for w in re.split(r"\s+", query.lower()) if len(w) > 1]

    scored = []
    for p in products:
        score = 0.0

        # Build searchable text
        kw_list = p.get("keywords", [])
        if isinstance(kw_list, str):           # safety: handle comma-string
            kw_list = [kw_list]
        searchable = " ".join([p["name"].lower()] + [k.lower() for k in kw_list])

        # 1) Full phrase match bonus (0 or +40)
        if query.lower() in p["name"].lower():
            score += 40

        # 2) Per-word coverage (0–30)
        if query_words:
            match_count = sum(1 for w in query_words if w in searchable)
            score += (match_count / len(query_words)) * 30

        # 3) Rating (0–20)
        score += (p.get("rating", 0) / 5) * 20

        # 4) Popularity (0–10)
        score += (p.get("popularity", 0) / 100) * 10

        scored.append({**p, "_score": round(score, 1)})

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored


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


# ═══════════════════════════════════════════════════════════════════════════════
# BOOTSTRAP  (build index once on startup)
# ═══════════════════════════════════════════════════════════════════════════════

trie          = Trie()
inv_index     = InvertedIndex()
cache         = SimpleCache(ttl_seconds=120)
product_map   = {p["id"]: p for p in PRODUCTS}

_seen: set[str] = set()
for product in PRODUCTS:
    all_terms = [product["name"]] + product.get("keywords", []) + [product.get("category", "")]
    inv_index.add(product["id"], all_terms)

    for term in [product["name"]] + product.get("keywords", []):
        if term not in _seen:
            _seen.add(term)
            trie.insert(term)

print(f"[search_service.py] Indexed {len(PRODUCTS)} products.")


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="SearchSphere Python Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    # 1) Candidate IDs via inverted index
    if q.strip():
        candidate_ids = inv_index.search(q)
    else:
        candidate_ids = set(product_map.keys())

    # 2) Hydrate products
    candidates = [product_map[pid] for pid in candidate_ids if pid in product_map]

    # 3) Filters
    if category and category.lower() != "all":
        candidates = [p for p in candidates if p.get("category", "").lower() == category.lower()]
    if min_price is not None:
        candidates = [p for p in candidates if p.get("price", 0) >= min_price]
    if max_price is not None:
        candidates = [p for p in candidates if p.get("price", 0) <= max_price]
    if min_rating is not None:
        candidates = [p for p in candidates if p.get("rating", 0) >= min_rating]

    # 4) Rank
    ranked = rank_products(candidates, q)

    # 5) Explicit sort override
    if sort == "price_asc":
        ranked.sort(key=lambda p: p.get("price", 0))
    elif sort == "price_desc":
        ranked.sort(key=lambda p: p.get("price", 0), reverse=True)
    elif sort == "rating":
        ranked.sort(key=lambda p: p.get("rating", 0), reverse=True)
    elif sort == "popularity":
        ranked.sort(key=lambda p: p.get("popularity", 0), reverse=True)

    cache.set(cache_key, ranked)
    return {"success": True, "count": len(ranked), "fromCache": False, "results": ranked}


# ── GET /autocomplete ─────────────────────────────────────────────────────────
@app.get("/autocomplete")
def autocomplete(q: str = Query(default="")):
    if not q.strip():
        return {"success": True, "suggestions": []}
    suggestions = trie.get_suggestions(q.strip())
    return {"success": True, "suggestions": suggestions}


# ── GET /recommendations/{id} ─────────────────────────────────────────────────
@app.get("/recommendations/{product_id}")
def recommendations(product_id: int):
    product = product_map.get(product_id)
    if not product:
        return {"success": False, "recommendations": []}

    scored = []
    for p in PRODUCTS:
        if p["id"] == product_id:
            continue
        score = 0

        # Same category → big bonus
        if p.get("category") == product.get("category"):
            score += 40

        # Price proximity (within ±50%) → up to +20
        base_price = product.get("price") or 1
        price_diff = abs(p.get("price", 0) - product.get("price", 0)) / base_price
        if price_diff < 0.5:
            score += 20 - math.floor(price_diff * 20)

        # Keyword overlap → +5 per shared keyword
        kw_a = set(product.get("keywords", []))
        kw_b = set(p.get("keywords", []))
        score += len(kw_a & kw_b) * 5

        scored.append({**p, "_score": score})

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return {"success": True, "recommendations": scored[:6]}


# ── GET /categories ───────────────────────────────────────────────────────────
@app.get("/categories")
def categories():
    cats = sorted({p.get("category", "") for p in PRODUCTS if p.get("category")})
    return {"success": True, "categories": cats}


# ── GET /health ───────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "products": len(PRODUCTS), "engine": "python-fastapi"}


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=False)
