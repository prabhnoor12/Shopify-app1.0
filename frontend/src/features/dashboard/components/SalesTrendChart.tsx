import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './SalesTrendChart.css';

export interface SalesTrendPoint {
  date: string;
  total_sales: number;
}


const SalesTrendChart: React.FC = () => {
  const [data, setData] = useState<SalesTrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSalesTrend = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get('/api/sales/trend');
        // Ensure we always store an array; sometimes backend might return an object
        setData(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        setError('Failed to load sales trend data.');
      } finally {
        setLoading(false);
      }
    };
    fetchSalesTrend();
  }, []);

  const totalSales = data.reduce((sum, d) => sum + (d.total_sales || 0), 0);
  const maxSales = Math.max(...(Array.isArray(data) ? data.map(d => d.total_sales) : []), 0);

  return (
    <div className="sales-trend-chart">
  <h2 className="sales-trend-title">Sales Trend (Last {Array.isArray(data) ? data.length : 0} Days)</h2>
      {error && <div className="dashboard-error">{error}</div>}
      <div className="sales-trend-summary">
        <span><strong>Total Sales:</strong> ${totalSales.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
  <span><strong>Days:</strong> {Array.isArray(data) ? data.length : 0}</span>
      </div>
      {loading ? (
        <div className="dashboard-loader" />
      ) : Array.isArray(data) && data.length === 0 ? (
        <div className="empty-state">
          <p>No sales data available.</p>
        </div>
      ) : (
        <table className="sales-trend-list">
          <thead>
            <tr>
              <th>#</th>
              <th>Date</th>
              <th>Total Sales</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(data) && data.map((point, idx) => (
              <tr key={point.date} className={`sales-trend-item${point.total_sales === maxSales ? ' sales-trend-item--highlight' : ''}`}>
                <td>{idx + 1}</td>
                <td>{point.date}</td>
                <td>${point.total_sales.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default SalesTrendChart;
