import './ProductTimelinePerformance.css';
import './AnalyticsCard.css';
import React, { memo } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export interface TimelinePerformanceData {
  date: string;
  views: number;
  adds_to_cart: number;
}

interface ProductTimelinePerformanceProps {
  timeline: TimelinePerformanceData[];
  loading?: boolean;
  error?: string | null;
}

const ProductTimelinePerformance: React.FC<ProductTimelinePerformanceProps> = memo(({ timeline, loading = false, error = null }) => {
  if (loading) {
    return (
      <div className="product-timeline-performance analytics-card" role="status" aria-busy="true">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#8884d8" strokeWidth="2" opacity="0.3"/><path d="M12 2a10 10 0 0 1 10 10" stroke="#8884d8" strokeWidth="2"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/></path></svg>
          Loading product timeline performance...
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="product-timeline-performance analytics-card" role="alert">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#ff4d4f" strokeWidth="2" opacity="0.3"/><path d="M12 8v4m0 4h.01" stroke="#ff4d4f" strokeWidth="2" strokeLinecap="round"/></svg>
          {error}
        </div>
      </div>
    );
  }
  if (!timeline || timeline.length === 0) {
    return (
      <div className="product-timeline-performance analytics-card" role="status">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#888" strokeWidth="2" opacity="0.2"/><path d="M8 12h8M12 8v8" stroke="#888" strokeWidth="2" strokeLinecap="round"/></svg>
          No product timeline data available.
        </div>
      </div>
    );
  }
  return (
    <div className="product-timeline-performance analytics-card">
      <h2 className="analytics-card-title">Product Timeline Performance (Last {timeline.length} Days)</h2>
      <div className="product-timeline-performance-chart-container analytics-card-section" aria-label="Product timeline chart">
        <ResponsiveContainer>
          <LineChart data={timeline} margin={{ top: 30, right: 40, left: 40, bottom: 30 }}>
            <XAxis dataKey="date" label={{ value: 'Date', position: 'insideBottom', offset: 14, style: { textAnchor: 'middle', fontSize: 15, fontWeight: 500 } }} tick={{ fontSize: 13, dy: 8 }} interval={0} padding={{ left: 8, right: 8 }} />
            <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft', offset: 18, style: { textAnchor: 'middle', fontSize: 15, fontWeight: 500, fill: '#23272f' } }} tick={{ fontSize: 13, dx: -8, fill: '#23272f' }} axisLine={{ stroke: '#bdbdbd', strokeWidth: 2 }} tickLine={{ stroke: '#bdbdbd', strokeWidth: 1 }} />
            <Tooltip />
            <Legend wrapperStyle={{ paddingTop: 10 }} />
            <Line type="monotone" dataKey="views" stroke="#8884d8" name="Views" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            <Line type="monotone" dataKey="adds_to_cart" stroke="#82ca9d" name="Adds to Cart" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="product-timeline-performance-table-wrapper analytics-card-section">
        <table className="product-timeline-performance-table" aria-label="Product timeline table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Views</th>
              <th>Adds to Cart</th>
            </tr>
          </thead>
          <tbody>
            {timeline.map((entry) => (
              <tr key={entry.date}>
                <td>{entry.date}</td>
                <td>{entry.views}</td>
                <td>{entry.adds_to_cart}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
});

export default ProductTimelinePerformance;
