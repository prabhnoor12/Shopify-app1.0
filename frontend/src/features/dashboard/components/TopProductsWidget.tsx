import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './TopProductsWidget.css';

interface TopProduct {
  product_id: number;
  title: string;
  total_sales?: number;
  orders?: number;
  views?: number;
  image_url?: string;
}

const TopProductsWidget: React.FC = () => {
  const [products, setProducts] = useState<TopProduct[]>([]);
  const [by, setBy] = useState<'sales' | 'views'>('sales');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(`/api/products/top?by=${by}`);
        // Normalize API response to an array to avoid reduce/map runtime errors
        setProducts(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        setError('Failed to load top products.');
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, [by]);

  const totalSales = by === 'sales' ? products.reduce((sum, p) => sum + (p.total_sales || 0), 0) : undefined;
  const totalOrders = by === 'sales' ? products.reduce((sum, p) => sum + (p.orders || 0), 0) : undefined;
  const totalViews = by === 'views' ? products.reduce((sum, p) => sum + (p.views || 0), 0) : undefined;

  return (
    <div className="top-products-widget">
      <h2 className="top-products-title">
        <span role="img" aria-label="trophy" className="top-products-trophy">🏆</span>
        Top Products ({by === 'sales' ? 'By Sales' : 'By Views'})
      </h2>

      <div className="top-products-toggle">
        <button
          className={`dashboard-btn top-products-toggle-btn${by === 'sales' ? ' active' : ''}`}
          onClick={() => setBy('sales')}
          disabled={by === 'sales'}
        >
          By Sales
        </button>
        <button
          className={`dashboard-btn top-products-toggle-btn${by === 'views' ? ' active' : ''}`}
          onClick={() => setBy('views')}
          disabled={by === 'views'}
        >
          By Views
        </button>
      </div>

      <div className="top-products-summary">
        {by === 'sales' && (
          <>
            <span><strong>Total Sales:</strong> ${totalSales?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            <span><strong>Total Orders:</strong> {totalOrders}</span>
          </>
        )}
        {by === 'views' && (
          <span><strong>Total Views:</strong> {totalViews}</span>
        )}
      </div>

      {error && <div className="dashboard-error">{error}</div>}
      {loading ? (
        <div className="dashboard-loader" />
      ) : products.length === 0 ? (
        <div className="empty-state">
          <p>No top products found.</p>
        </div>
      ) : (
        <table className="top-products-list">
          <thead>
            <tr>
              <th>#</th>
              <th>Product</th>
              {by === 'sales' && <th>Total Sales</th>}
              {by === 'sales' && <th>Orders</th>}
              {by === 'views' && <th>Views</th>}
            </tr>
          </thead>
          <tbody>
            {products.map((p, idx) => (
              <tr key={p.product_id} className={`top-product-item${idx === 0 ? ' top-product-item--highlight' : ''}`}>
                <td>{idx + 1}</td>
                <td className="top-product-td-flex">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.title} className="top-product-img" />
                  ) : (
                    <span className="top-product-img top-product-img--placeholder">🛒</span>
                  )}
                  <span>{p.title}</span>
                </td>
                {by === 'sales' && <td>${p.total_sales?.toFixed(2) ?? '0.00'}</td>}
                {by === 'sales' && <td>{p.orders ?? 0}</td>}
                {by === 'views' && <td>{p.views ?? 0}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default TopProductsWidget;
