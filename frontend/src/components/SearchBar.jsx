import { useState, useEffect, useRef } from "react";

const API = "http://localhost:5000";

export default function SearchBar({ onSearch }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceRef = useRef(null);
  const wrapperRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleChange(e) {
    const val = e.target.value;
    setQuery(val);

    clearTimeout(debounceRef.current);
    if (val.trim().length < 1) {
      setSuggestions([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`${API}/api/autocomplete?q=${encodeURIComponent(val)}`);
        const data = await res.json();
        setSuggestions(data.suggestions || []);
        setShowSuggestions(true);
      } catch {
        setSuggestions([]);
      }
    }, 200);
  }

  function handleSubmit(e) {
    e?.preventDefault();
    setShowSuggestions(false);
    onSearch(query);
  }

  function handleSuggestionClick(s) {
    setQuery(s);
    setShowSuggestions(false);
    onSearch(s);
  }

  function handleClear() {
    setQuery("");
    setSuggestions([]);
    onSearch("");
  }

  return (
    <form className="search-wrapper" onSubmit={handleSubmit} ref={wrapperRef}>
      <div className="search-bar">
        <img src="/search.jpg" className="search-icon" alt="SearchSphere" />
        <input
          id="main-search-input"
          className="search-input"
          type="text"
          value={query}
          onChange={handleChange}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder="Search for laptops, headphones, shoes…"
          autoComplete="off"
        />
        {query && (
          <button type="button" className="clear-btn" onClick={handleClear} aria-label="Clear search">
            ✕
          </button>
        )}
        <button type="submit" className="search-btn">Search</button>
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <div className="suggestions-dropdown" role="listbox">
          {suggestions.map((s, i) => (
            <div
              key={i}
              className="suggestion-item"
              role="option"
              onClick={() => handleSuggestionClick(s)}
            >
              <span className="suggestion-icon">🔎</span>
              {s}
            </div>
          ))}
        </div>
      )}
    </form>
  );
}
