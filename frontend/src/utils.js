// Returns an emoji icon by category
export function getCategoryEmoji(category) {
  const map = {
    Electronics: "💻",
    Computers: "🖥️",
    Gaming: "🎮",
    Photography: "📷",
    Wearables: "⌚",
    Footwear: "👟",
    Clothing: "👕",
    "Smart Home": "🏠",
    "Home Appliances": "🏡",
    Kitchen: "🍳",
    Sports: "🏋️",
    Accessories: "🎧",
    Networking: "📡",
    Office: "🪑",
    Travel: "✈️",
  };
  return map[category] || "📦";
}

// Render star string
export function renderStars(rating) {
  const full = Math.floor(rating);
  const half = rating % 1 >= 0.5 ? 1 : 0;
  return "★".repeat(full) + (half ? "½" : "") + "☆".repeat(5 - full - half);
}
