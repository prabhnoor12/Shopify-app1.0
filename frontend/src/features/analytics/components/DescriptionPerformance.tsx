import './DescriptionPerformance.css';
import './AnalyticsCard.css';
import React, { memo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export interface VariantPerformance {
  variant_id: number;
  description: string;
  impressions: number;
  clicks: number;
  conversions: number;
  conversion_rate: number;
  confidence_interval: [number, number];
  lift_over_baseline: number;
  is_baseline: boolean;
  estimated_revenue: number;
  p_value?: number | null;
}

interface DescriptionPerformanceProps {
  variants: VariantPerformance[];
  loading?: boolean;
  error?: string | null;
}

const DescriptionPerformance: React.FC<DescriptionPerformanceProps> = memo(({ variants, loading = false, error = null }) => {
  if (loading) {
    return (
      <div className="description-performance analytics-card" role="status" aria-busy="true">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#8884d8" strokeWidth="2" opacity="0.3"/><path d="M12 2a10 10 0 0 1 10 10" stroke="#8884d8" strokeWidth="2"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/></path></svg>
          Loading description performance...
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="description-performance analytics-card" role="alert">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#ff4d4f" strokeWidth="2" opacity="0.3"/><path d="M12 8v4m0 4h.01" stroke="#ff4d4f" strokeWidth="2" strokeLinecap="round"/></svg>
          {error}
        </div>
      </div>
    );
  }
  if (!variants || variants.length === 0) {
    return (
      <div className="description-performance analytics-card" role="status">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#888" strokeWidth="2" opacity="0.2"/><path d="M8 12h8M12 8v8" stroke="#888" strokeWidth="2" strokeLinecap="round"/></svg>
          No description performance data available.
        </div>
      </div>
    );
  }
  return (
    <div className="description-performance analytics-card">
      <h2 className="analytics-card-title">Description Performance (A/B Test)</h2>
      <div className="description-performance-chart-container analytics-card-section" aria-label="Description performance chart">
        <ResponsiveContainer>
          <BarChart data={variants} margin={{ top: 30, right: 40, left: 60, bottom: 40 }}>
            <XAxis
              dataKey="variant_id"
              label={{ value: 'Variant ID', position: 'insideBottom', offset: 8, style: { textAnchor: 'middle', fontSize: 15, fontWeight: 500 } }}
              tick={{ fontSize: 13, dy: 8 }}
              interval={0}
              padding={{ left: 8, right: 8 }}
            />
            <YAxis
              label={{ value: 'Count', angle: -90, position: 'insideLeft', offset: 5, style: { textAnchor: 'middle', fontSize: 15, fontWeight: 500, fill: '#23272f', background: '#fff' } }}
              tick={{ fontSize: 13, dx: -8, fill: '#23272f' }}
              axisLine={{ stroke: '#bdbdbd', strokeWidth: 2 }}
              tickLine={{ stroke: '#bdbdbd', strokeWidth: 1 }}
            />
            <Tooltip />
            <Legend wrapperStyle={{ paddingTop: 10 }} />
            <Bar dataKey="impressions" fill="#8884d8" name="Impressions" />
            <Bar dataKey="clicks" fill="#82ca9d" name="Clicks" />
            <Bar dataKey="conversions" fill="#ffc658" name="Conversions" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="description-performance-table-wrapper analytics-card-section">
        <table className="description-performance-table" aria-label="Description performance table">
          <thead>
            <tr>
              <th>Variant ID</th>
              <th>Description</th>
              <th>Impressions</th>
              <th>Clicks</th>
              <th>Conversions</th>
              <th>Conversion Rate (%)</th>
              <th>Confidence Interval (%)</th>
              <th>Lift Over Baseline (%)</th>
              <th>Estimated Revenue</th>
              <th>P-Value</th>
              <th>Baseline</th>
            </tr>
          </thead>
          <tbody>
            {variants.map((v) => (
              <tr key={v.variant_id} className={v.is_baseline ? 'baseline' : ''}>
                <td>{v.variant_id}</td>
                <td>{v.description}</td>
                <td>{v.impressions}</td>
                <td>{v.clicks}</td>
                <td>{v.conversions}</td>
                <td>{v.conversion_rate.toFixed(2)}</td>
                <td>{v.confidence_interval[0].toFixed(2)} - {v.confidence_interval[1].toFixed(2)}</td>
                <td>{v.lift_over_baseline.toFixed(2)}</td>
                <td>${v.estimated_revenue.toFixed(2)}</td>
                <td>{v.p_value !== undefined && v.p_value !== null ? v.p_value.toFixed(4) : '-'}</td>
                <td>{v.is_baseline ? 'Yes' : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
});

export default DescriptionPerformance;
