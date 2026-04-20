export default function Filters({ categories, filters, onFilterChange, onClose }) {
  function handleReset() {
    onFilterChange({ category: "All", minPrice: "", maxPrice: "", minRating: "" });
  }

  return (
    <>
      {/* Dark overlay — click to close */}
      <div className="filters-overlay" onClick={onClose} />

      {/* Slide-in drawer */}
      <div className="filters-drawer" role="dialog" aria-label="Filter products">
        <div className="drawer-header">
          <span className="drawer-title">Filters</span>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <button className="reset-btn" onClick={handleReset}>Reset all</button>
            <button className="drawer-close-btn" onClick={onClose} aria-label="Close filters">✕</button>
          </div>
        </div>

        {/* Category */}
        <div className="filter-group">
          <label className="filter-label" htmlFor="filter-category">Category</label>
          <select
            id="filter-category"
            className="filter-select"
            value={filters.category}
            onChange={(e) => onFilterChange({ ...filters, category: e.target.value })}
          >
            <option value="All">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <hr className="filter-divider" />

        {/* Price Range */}
        <div className="filter-group">
          <label className="filter-label">Price Range ($)</label>
          <div className="price-inputs">
            <input
              className="price-input"
              type="number"
              min="0"
              placeholder="Min"
              value={filters.minPrice}
              onChange={(e) => onFilterChange({ ...filters, minPrice: e.target.value })}
            />
            <input
              className="price-input"
              type="number"
              min="0"
              placeholder="Max"
              value={filters.maxPrice}
              onChange={(e) => onFilterChange({ ...filters, maxPrice: e.target.value })}
            />
          </div>
        </div>

        <hr className="filter-divider" />

        {/* Minimum Rating */}
        <div className="filter-group">
          <label className="filter-label">Minimum Rating</label>
          <div className="rating-options">
            {[4.5, 4.0, 3.5, 0].map((val) => (
              <label key={val} className="rating-option">
                <input
                  type="radio"
                  name="minRating"
                  value={val}
                  checked={Number(filters.minRating) === val || (val === 0 && filters.minRating === "")}
                  onChange={() => onFilterChange({ ...filters, minRating: val === 0 ? "" : val })}
                />
                {val === 0 ? (
                  <span>Any Rating</span>
                ) : (
                  <>
                    <span className="stars-display">{"★".repeat(Math.floor(val))}</span>
                    <span>{val}+</span>
                  </>
                )}
              </label>
            ))}
          </div>
        </div>

        <button className="apply-filters-btn" onClick={onClose}>
          Apply & Close
        </button>
      </div>
    </>
  );
}
