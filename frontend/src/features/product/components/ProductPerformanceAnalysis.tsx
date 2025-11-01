
import React, { useEffect, useState } from 'react';
import { fetchProducts } from '../../../api/productApi';
import { fetchRevenueAttribution, fetchProductTimelinePerformance } from '../../../api/analyticsApi';
import './ProductPerformanceAnalysis.css';

interface Product {
  id: string;
  name: string;
  description?: string;
  imageUrl?: string;
  price?: number;
}

interface PerformanceMetrics {
  sales?: number;
  revenue?: number;
  conversionRate?: number;
  views?: number;
  timeline?: Array<{ date: string; sales: number; revenue: number }>;
}

const ProductPerformanceAnalysis: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);
  const [metrics, setMetrics] = useState<Record<string, PerformanceMetrics>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<{ from: string; to: string }>({ from: '', to: '' });
  const [notification, setNotification] = useState<string>('');

  useEffect(() => {
    fetchProducts()
      .then(data => setProducts(data))
      .catch(() => setError('Failed to fetch products'));
  }, []);

  const handleProductSelect = (id: string) => {
    setSelectedProductIds(prev =>
      prev.includes(id) ? prev.filter(pid => pid !== id) : [...prev, id]
    );
  };

  const handleAnalyze = async () => {
    if (selectedProductIds.length === 0) return;
    setLoading(true);
    setError(null);
    let newMetrics: Record<string, PerformanceMetrics> = {};
    try {
      for (const productId of selectedProductIds) {
        const revenue = await fetchRevenueAttribution(productId);
        const timeline = await fetchProductTimelinePerformance(productId);
        newMetrics[productId] = {
          sales: revenue.sales,
          revenue: revenue.revenue,
          conversionRate: revenue.conversionRate,
          views: revenue.views,
          timeline: timeline.timeline,
        };
      }
      setMetrics(newMetrics);
      setNotification('Analysis complete');
    } catch (err) {
      setError('Failed to analyze product performance');
    } finally {
      setLoading(false);
      setTimeout(() => setNotification(''), 2000);
    }
  };

  // Filter products by name
  const [filter, setFilter] = useState('');
  const filteredProducts = Array.isArray(products)
    ? products.filter(product => product.name.toLowerCase().includes(filter.toLowerCase()))
    : [];

  // Export as CSV
  const handleExportCSV = () => {
    if (Object.keys(metrics).length === 0) return;
    const rows = [
      ['Product', 'Sales', 'Revenue', 'Conversion Rate', 'Views'],
      ...selectedProductIds.map(pid => {
        const m = metrics[pid] || {};
        return [
          products.find(p => p.id === pid)?.name || pid,
          m.sales ?? '',
          m.revenue ?? '',
          m.conversionRate ?? '',
          m.views ?? ''
        ];
      })
    ];
    const csv = rows.map(row => row.map(String).join(',')).join('\n');
    navigator.clipboard.writeText(csv);
    setNotification('CSV copied to clipboard');
    setTimeout(() => setNotification(''), 2000);
  };

  return (
    <div className="product-performance-analysis">
      <h2>Product Performance Analysis</h2>
      <div className="ppa-form">
        <input
          type="text"
          placeholder="Filter products by name..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="ppa-filter"
        />
        <div className="ppa-product-list">
          {Array.isArray(filteredProducts) && filteredProducts.map(product => (
            <label key={product.id} className="ppa-product-item">
              <input
                type="checkbox"
                checked={selectedProductIds.includes(product.id)}
                onChange={() => handleProductSelect(product.id)}
              />
              {product.name}
            </label>
          ))}
        </div>
        <div className="ppa-date-range">
          <label>
            From:
            <input
              type="date"
              value={dateRange.from}
              onChange={e => setDateRange(r => ({ ...r, from: e.target.value }))}
            />
          </label>
          <label>
            To:
            <input
              type="date"
              value={dateRange.to}
              onChange={e => setDateRange(r => ({ ...r, to: e.target.value }))}
            />
          </label>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={selectedProductIds.length === 0 || loading}
          className="ppa-btn"
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
        <button
          onClick={handleExportCSV}
          disabled={Object.keys(metrics).length === 0}
          className="ppa-btn"
        >
          Export CSV
        </button>
      </div>
      {notification && <div className="ppa-notification">{notification}</div>}
      {error && <div className="ppa-error">{error}</div>}
      {Object.keys(metrics).length > 0 && (
        <div className="ppa-results">
          <h3>Performance Comparison</h3>
          <table className="ppa-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Sales</th>
                <th>Revenue</th>
                <th>Conversion Rate</th>
                <th>Views</th>
              </tr>
            </thead>
            <tbody>
              {selectedProductIds.map(pid => {
                const m = metrics[pid] || {};
                return (
                  <tr key={pid}>
                    <td>{products.find(p => p.id === pid)?.name || pid}</td>
                    <td>{m.sales ?? '-'}</td>
                    <td>{m.revenue ?? '-'}</td>
                    <td>{m.conversionRate ?? '-'}</td>
                    <td>{m.views ?? '-'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ProductPerformanceAnalysis;
