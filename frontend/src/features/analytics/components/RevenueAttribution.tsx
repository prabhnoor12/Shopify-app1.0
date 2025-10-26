import './RevenueAttribution.css';
import './AnalyticsCard.css';
import React, { memo } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export interface RevenueAttributionData {
  product_id: number;
  total_revenue: number;
  total_subtotal: number;
  total_tax: number;
  total_discounts: number;
  total_orders: number;
  average_order_value: number;
}

interface RevenueAttributionProps {
  data?: RevenueAttributionData | null;
  loading?: boolean;
  error?: string | null;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

const RevenueAttribution: React.FC<RevenueAttributionProps> = memo(({ data, loading = false, error = null }) => {
  if (loading) {
    return (
      <div className="revenue-attribution analytics-card" role="status" aria-busy="true">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#8884d8" strokeWidth="2" opacity="0.3"/><path d="M12 2a10 10 0 0 1 10 10" stroke="#8884d8" strokeWidth="2"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/></path></svg>
          Loading revenue attribution...
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="revenue-attribution analytics-card" role="alert">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#ff4d4f" strokeWidth="2" opacity="0.3"/><path d="M12 8v4m0 4h.01" stroke="#ff4d4f" strokeWidth="2" strokeLinecap="round"/></svg>
          {error}
        </div>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="revenue-attribution analytics-card" role="status">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#888" strokeWidth="2" opacity="0.2"/><path d="M8 12h8M12 8v8" stroke="#888" strokeWidth="2" strokeLinecap="round"/></svg>
          No revenue attribution data available.
        </div>
      </div>
    );
  }
  const pieData = [
    { name: 'Subtotal', value: data.total_subtotal },
    { name: 'Tax', value: data.total_tax },
    { name: 'Discounts', value: data.total_discounts },
  ];
  return (
    <div className="revenue-attribution analytics-card">
      <h2 className="analytics-card-title">Revenue Attribution</h2>
      <div className="revenue-attribution-metrics">
        <div className="revenue-attribution-metric-card">
          <div className="revenue-attribution-metric-label">Total Revenue</div>
          <div className="revenue-attribution-metric-value positive">${data.total_revenue.toFixed(2)}</div>
        </div>
        <div className="revenue-attribution-metric-card">
          <div className="revenue-attribution-metric-label">Average Order Value</div>
          <div className="revenue-attribution-metric-value">${data.average_order_value.toFixed(2)}</div>
        </div>
        <div className="revenue-attribution-metric-card">
          <div className="revenue-attribution-metric-label">Total Orders</div>
          <div className="revenue-attribution-metric-value">{data.total_orders}</div>
        </div>
      </div>
      <div className="revenue-attribution-chart-container analytics-card-section" aria-label="Revenue breakdown chart">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
              {pieData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="analytics-card-section revenue-attribution-table-wrapper">
        <table className="revenue-attribution-table" aria-label="Revenue attribution table">
          <tbody>
            <tr>
              <td>Product ID</td>
              <td>{data.product_id}</td>
            </tr>
            <tr>
              <td>Total Revenue</td>
              <td>${data.total_revenue.toFixed(2)}</td>
            </tr>
            <tr>
              <td>Total Subtotal</td>
              <td>${data.total_subtotal.toFixed(2)}</td>
            </tr>
            <tr>
              <td>Total Tax</td>
              <td>${data.total_tax.toFixed(2)}</td>
            </tr>
            <tr>
              <td>Total Discounts</td>
              <td className="revenue-attribution-metric-value negative">${data.total_discounts.toFixed(2)}</td>
            </tr>
            <tr>
              <td>Total Orders</td>
              <td>{data.total_orders}</td>
            </tr>
            <tr>
              <td>Average Order Value</td>
              <td>${data.average_order_value.toFixed(2)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
});

export default RevenueAttribution;
