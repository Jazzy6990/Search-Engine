import { getCategoryEmoji, renderStars } from "../utils";

export default function ProductCard({ product, onSelect, compact = false }) {
  const emoji = getCategoryEmoji(product.category);
  const stars = renderStars(product.rating);

  return (
    <article
      className="product-card"
      onClick={() => onSelect && onSelect(product)}
      title={product.name}
    >
      <div className="card-image">
        <span>{emoji}</span>
        <span className="card-category-badge">{product.category}</span>
        {!compact && product._score !== undefined && (
          <span className="score-badge">Score {product._score}</span>
        )}
      </div>

      <div className="card-body">
        <h3 className="card-name">{product.name}</h3>

        <div className="card-meta">
          <div className="card-rating">
            <span className="stars">{stars}</span>
            <span className="rating-val">{product.rating}</span>
          </div>
          {!compact && (
            <>
              <span className="popularity-dot" title="Popularity" />
              <span className="popularity-val">{product.popularity}% popular</span>
            </>
          )}
        </div>

        <div className="card-footer">
          <span className="card-price">${product.price.toFixed(2)}</span>
          <button
            className="add-btn"
            onClick={(e) => {
              e.stopPropagation();
              alert(`Added "${product.name}" to cart!`);
            }}
          >
            + Add
          </button>
        </div>
      </div>
    </article>
  );
}
