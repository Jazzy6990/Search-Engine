import sqlite3
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "search.db"
JSON_PATH = BASE_DIR / "data" / "products.json"

def setup_database():
    # Remove existing DB if it exists to start fresh
    if DB_PATH.exists():
        DB_PATH.unlink()
        
    print(f"Creating database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create standard table to hold product details
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL,
            rating REAL,
            popularity INTEGER,
            keywords TEXT
        )
    """)

    # 2. Create FTS5 virtual table for full-text search.
    # We include name, category, and keywords for searching.
    # The 'content' option links it directly to the 'products' table.
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
            name,
            category,
            keywords,
            content='products',
            content_rowid='id'
        )
    """)

    # 3. Read products from JSON
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Inserting {len(products)} products into SQLite...")

    # 4. Insert into both tables
    for p in products:
        # Convert keywords list to a space-separated string for searching
        keywords_str = " ".join(p.get("keywords", [])) if isinstance(p.get("keywords"), list) else p.get("keywords", "")
        
        cursor.execute("""
            INSERT INTO products (id, name, category, price, rating, popularity, keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (p["id"], p["name"], p["category"], p["price"], p["rating"], p["popularity"], keywords_str))

        # Also insert into the FTS table so it gets indexed immediately
        cursor.execute("""
            INSERT INTO products_fts (rowid, name, category, keywords)
            VALUES (?, ?, ?, ?)
        """, (p["id"], p["name"], p["category"], keywords_str))

    conn.commit()
    conn.close()
    print("Database setup complete! SQLite FTS5 index is ready.")

if __name__ == "__main__":
    setup_database()
