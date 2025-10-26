import './CategoryPerformance.css';
import './AnalyticsCard.css';
import React, { memo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useQuery } from '@tanstack/react-query';
// Update the import path if the file is named differently, e.g., 'analyticsApi.ts'
import { fetchCategoryPerformance } from '../../../api/analyticsApi';

export interface CategoryPerformanceData {
  category: string;
  product_count: number;
  total_views: number;
  total_conversions: number;
  average_conversion_rate: number;
}

interface CategoryPerformanceProps {
  categories?: CategoryPerformanceData[];
  loading?: boolean;
  error?: string | null;
}




// Helper: Aggregate categories for chart (top N + 'Other')
function aggregateCategories(data: CategoryPerformanceData[], topN = 10): CategoryPerformanceData[] {
  if (!data || data.length <= topN) return data;
  const sorted = [...data].sort((a, b) => b.total_views - a.total_views);
  const top = sorted.slice(0, topN);
  const other = sorted.slice(topN);
  const otherAgg = other.reduce(
    (acc, cur) => {
      acc.product_count += cur.product_count;
      acc.total_views += cur.total_views;
      acc.total_conversions += cur.total_conversions;
      acc.average_conversion_rate += cur.average_conversion_rate;
      return acc;
    },
    {
      category: 'Other',
      product_count: 0,
      total_views: 0,
      total_conversions: 0,
      average_conversion_rate: 0,
    }
  );
  if (other.length > 0) {
    otherAgg.average_conversion_rate = otherAgg.average_conversion_rate / other.length;
    return [...top, otherAgg];
  }
  return top;
}

// Now using real API call from categoryPerformanceApi

const CategoryPerformance: React.FC<CategoryPerformanceProps> = memo(({ categories: propCategories, loading: propLoading = false, error: propError = null }) => {
  // Use react-query for async fetch
  const { data: categories, isLoading, isError, error } = useQuery<CategoryPerformanceData[], Error>({
    queryKey: ['category-performance'],
    queryFn: fetchCategoryPerformance,
    enabled: !propCategories,
  });
  const displayCategories = propCategories || categories || [];
  const chartCategories = aggregateCategories(displayCategories, 10);

  return (
    <section className="category-performance analytics-card" aria-label="Category Performance">
      <h2 className="analytics-card-title">Category Performance</h2>
      {propLoading || isLoading ? (
        <div className="analytics-card-empty" role="status" aria-busy="true">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#8884d8" strokeWidth="2" opacity="0.3"/><path d="M12 2a10 10 0 0 1 10 10" stroke="#8884d8" strokeWidth="2"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/></path></svg>
          Loading category performance...
        </div>
      ) : propError || isError ? (
        <div className="analytics-card-empty" role="alert">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#ff4d4f" strokeWidth="2" opacity="0.3"/><path d="M12 8v4m0 4h.01" stroke="#ff4d4f" strokeWidth="2" strokeLinecap="round"/></svg>
          {propError || (error as Error)?.message}
        </div>
      ) : displayCategories.length === 0 ? (
        <div className="analytics-card-empty" role="status">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#888" strokeWidth="2" opacity="0.2"/><path d="M8 12h8M12 8v8" stroke="#888" strokeWidth="2" strokeLinecap="round"/></svg>
          No category performance data available.
        </div>
      ) : (
        <>
          <div className="category-performance-chart-container analytics-card-section" aria-label="Category performance chart">
            <ResponsiveContainer>
              <BarChart data={chartCategories} margin={{ top: 20, right: 30, left: 24, bottom: 32 }}>
                <XAxis
                  dataKey="category"
                  label={{ value: 'Category', position: 'outsideBottom', offset: 8, style: { fontSize: 15, fontWeight: 600, fill: '#23272f' } }}
                  tick={{ fontSize: 13, fontWeight: 500, fill: '#23272f' }}
                />
                <YAxis
                  label={{ value: 'Count', angle: -90, position: 'insideLeft', offset: 10, style: { fontSize: 15, fontWeight: 600, fill: '#23272f', paddingLeft: 0 } }}
                  tick={{ fontSize: 13, fontWeight: 500, fill: '#23272f' }}
                />
                <Tooltip />
                <Legend wrapperStyle={{ marginTop: 18, fontSize: 15, fontWeight: 600 }} className="category-performance-legend" />
                <Bar dataKey="total_views" fill="#4f8cff" name="Total Views" />
                <Bar dataKey="total_conversions" fill="#ff69b4" name="Total Conversions" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="category-performance-table-wrapper analytics-card-section">
            <table className="category-performance-table" aria-label="Category performance table">
              <thead>
                <tr>
                  <th scope="col">Category</th>
                  <th scope="col">Product Count</th>
                  <th scope="col">Total Views</th>
                  <th scope="col">Total Conversions</th>
                  <th scope="col">Avg. Conversion Rate (%)</th>
                </tr>
              </thead>
              <tbody>
                {displayCategories.map((c) => (
                  <tr key={c.category}>
                    <td>{c.category}</td>
                    <td>{c.product_count}</td>
                    <td>{c.total_views}</td>
                    <td>{c.total_conversions}</td>
                    <td>{c.average_conversion_rate.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
});

export default CategoryPerformance;
