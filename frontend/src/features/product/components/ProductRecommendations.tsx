
import React, { useEffect, useState } from 'react';
import { abTestingApi } from '../../../api/abTestingApi';
import './ProductRecommendations.css';

interface Recommendation {
  id: string;
  name: string;
  description?: string;
  imageUrl?: string;
  reason?: string;
  price?: number;
}


import { fetchProducts } from '../../../api/productApi';

const ProductRecommendations: React.FC = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [allProducts, setAllProducts] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [priceRange, setPriceRange] = useState<{ min: number; max: number }>({ min: 0, max: 10000 });

  useEffect(() => {
    Promise.all([
      abTestingApi.getGeneralRecommendations(),
      fetchProducts()
    ])
      .then(([recData, prodData]) => {
        setRecommendations(recData.recommendations || []);
        setAllProducts(prodData || []);
      })
      .catch(() => setError('Failed to fetch recommendations'))
      .finally(() => setLoading(false));
  }, []);

  // Advanced filtering logic
  const filteredRecommendations = recommendations
    .filter(rec =>
      (!filter || rec.name.toLowerCase().includes(filter.toLowerCase())) &&
      (!category || (rec as any).category === category) &&
      (!rec.price || (rec.price >= priceRange.min && rec.price <= priceRange.max))
    )
    .sort((a, b) => (b.reason?.length ?? 0) - (a.reason?.length ?? 0)) // Example: prioritize by reason length
    .slice(0, 8); // Show top 8 recommendations

  // Extract categories from all products
  const categories = Array.from(new Set(allProducts.map(p => (p as any).category).filter(Boolean)));

  if (loading) return <div className="product-recommendations-loading">Loading recommendations...</div>;
  if (error) return <div className="product-recommendations-error">{error}</div>;

  return (
    <div className="product-recommendations">
      <h3>Related Product Recommendations</h3>
      <div className="product-recommendations-filters">
        <input
          type="text"
          placeholder="Filter by name..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="product-recommendations-filter"
        />
  <label htmlFor="recommendation-category-select" className="visually-hidden">Category</label>
        <select
          id="recommendation-category-select"
          title="Filter by category"
          value={category}
          onChange={e => setCategory(e.target.value)}
          className="product-recommendations-category"
        >
          <option value="">All Categories</option>
          {Array.isArray(categories) && categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <label>
          Price:
          <input
            type="number"
            value={priceRange.min}
            min={0}
            max={priceRange.max}
            onChange={e => setPriceRange(r => ({ ...r, min: Number(e.target.value) }))}
            className="product-recommendations-price-input"
          />
          -
          <input
            type="number"
            value={priceRange.max}
            min={priceRange.min}
            onChange={e => setPriceRange(r => ({ ...r, max: Number(e.target.value) }))}
            className="product-recommendations-price-input"
          />
        </label>
      </div>
      {!Array.isArray(filteredRecommendations) || filteredRecommendations.length === 0 ? (
        <div className="product-recommendations-empty">No recommendations found.</div>
      ) : (
        <ul className="product-recommendations-list">
          {filteredRecommendations.map(rec => (
            <li key={rec.id} className="product-recommendation-item">
              {rec.imageUrl && (
                <img src={rec.imageUrl} alt={rec.name} className="product-recommendation-image" />
              )}
              <div className="product-recommendation-info">
                <strong>{rec.name}</strong>
                {rec.description && <p>{rec.description}</p>}
                {rec.reason && <p className="product-recommendation-reason">Why: {rec.reason}</p>}
                {(rec as any).category && <p className="product-recommendation-category">Category: {(rec as any).category}</p>}
                {rec.price !== undefined && <p className="product-recommendation-price">Price: ${rec.price}</p>}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ProductRecommendations;
