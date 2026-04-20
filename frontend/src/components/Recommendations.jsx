import { useEffect, useState } from "react";
import ProductCard from "./ProductCard";

const API = "http://localhost:5000";

export default function Recommendations({ productId, onSelect }) {
  const [recs, setRecs] = useState([]);

  useEffect(() => {
    if (!productId) return;
    fetch(`${API}/api/recommendations/${productId}`)
      .then((r) => r.json())
      .then((d) => setRecs(d.recommendations || []))
      .catch(() => setRecs([]));
  }, [productId]);

  if (recs.length === 0) return null;

  return (
    <div className="recommendations-section">
      <h2 className="section-title">
        <span className="section-title-icon">✨</span>
        You Might Also Like
      </h2>
      <div className="rec-grid">
        {recs.map((p) => (
          <ProductCard key={p.id} product={p} onSelect={onSelect} compact />
        ))}
      </div>
    </div>
  );
}
