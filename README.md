# SearchSphere 🔍

A high-performance product search engine built to demonstrate core search algorithms (Inverted Index, Prefix Tries, Custom Ranking) from scratch, without relying on a full database or third-party search engines like Elasticsearch.

## 🚀 Features

- **Inverted Index**: Maps every query keyword directly to matching product IDs for `O(1)` lookups. Supports `AND` search with an `OR` fallback.
- **Prefix Trie Autocomplete**: Provides instantaneous real-time search suggestions as you type.
- **Custom Ranking Algorithm**: Ranks results dynamically based on phrase matches, keyword coverage, product ratings, and overall popularity.
- **In-Memory Cache**: Reduces load times for frequent searches with a monotonic TTL cache.
- **Smart Recommendations**: Suggests products based on category match, similar price points, and shared keywords.
- **Premium Dark UI**: A sleek, black-and-white, highly-responsive frontend interface.

## 🏗️ Architecture

The system is split into three layers:

1. **Frontend (Vite + React)** 
   - Clean, UI fetching data from the API gateway.
   - Runs on port `5173`.
2. **API Gateway (Node.js + Express)** 
   - A thin layer that receives frontend requests and proxies them.
   - Runs on port `5000`.
3. **Core Search Logic (Python + FastAPI)**
   - Holds the in-memory dataset, Trie, and Inverted Index algorithms.
   - Runs on port `5001`.

## 🛠️ Getting Started

To run the application locally, you will need **three separate terminal windows**:

### 1. Start the Python Search Engine
This runs the core search logic layer.
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn services.search_service:app --host 0.0.0.0 --port 5001
```

### 2. Start the Express Gateway
This serves as the API gateway the frontend communicates with.
```bash
cd backend
npm install
npm start
```

### 3. Start the React Frontend
This starts the user interface.
```bash
cd frontend
npm install
npm run dev
```

Once all three processes are running, open your web browser and navigate to:
**http://localhost:5173**

## 📂 Project Structure

```text
D:\Search Engine
├── backend/
│   ├── data/
│   │   └── products.json           # Mock catalog of 85 products
│   ├── services/
│   │   └── search_service.py       # Core Python logic (Trie, Inverted Index)
│   ├── server.js                   # Node/Express API Gateway
│   └── requirements.txt            # Python dependencies (FastAPI, Uvicorn)
├── frontend/
│   ├── public/                     # Static assets (images, icons)
│   ├── src/
│   │   ├── components/             # React UI components (SearchBar, Filters, etc.)
│   │   ├── App.jsx                 # Main React Application
│   │   └── index.css               # Black and white dark theme CSS
│   └── package.json
└── README.md                       # Documentation
```
