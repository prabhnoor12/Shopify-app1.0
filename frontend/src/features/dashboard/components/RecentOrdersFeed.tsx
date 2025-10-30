
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './RecentOrdersFeed.css';

export interface RecentOrder {
  order_id: number;
  created_at: string;
  customer: string;
  product_id: number;
  total_price: number;
  product_title?: string;
  product_image_url?: string;
}



const RecentOrdersFeed: React.FC = () => {
  const [orders, setOrders] = useState<RecentOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrders = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get('/api/orders/recent');
        // Ensure we always store an array (guard against malformed API responses)
        setOrders(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        setError('Failed to load recent orders.');
      } finally {
        setLoading(false);
      }
    };
    fetchOrders();
  }, []);

  const totalRevenue = orders.reduce((sum, o) => sum + (o.total_price || 0), 0);

  return (
    <div className="recent-orders-feed">
      <h2 className="recent-orders-title">Recent Orders</h2>
      {error && <div className="dashboard-error">{error}</div>}
      <div className="recent-orders-summary">
        <span><strong>Total Revenue:</strong> ${totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
        <span><strong>Orders:</strong> {orders.length}</span>
      </div>
      {loading ? (
        <div className="dashboard-loader" />
      ) : orders.length === 0 ? (
        <div className="empty-state">
          <p>No recent orders found.</p>
        </div>
      ) : (
        <table className="recent-orders-list">
          <thead>
            <tr>
              <th>#</th>
              <th>Product</th>
              <th>Order ID</th>
              <th>Date</th>
              <th>Customer</th>
              <th>Total Price</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o, idx) => (
              <tr key={o.order_id} className={`recent-order-item${idx === 0 ? ' recent-order-item--highlight' : ''}`}>
                <td>{idx + 1}</td>
                <td className="recent-order-td-flex">
                  {o.product_image_url ? (
                    <img src={o.product_image_url} alt={o.product_title || 'Product'} className="recent-order-img" />
                  ) : (
                    <span className="recent-order-img recent-order-img--placeholder">🛒</span>
                  )}
                  <span>{o.product_title || o.product_id}</span>
                </td>
                <td>{o.order_id}</td>
                <td>{new Date(o.created_at).toLocaleString()}</td>
                <td>{o.customer}</td>
                <td>${(o.total_price ?? 0).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default RecentOrdersFeed
