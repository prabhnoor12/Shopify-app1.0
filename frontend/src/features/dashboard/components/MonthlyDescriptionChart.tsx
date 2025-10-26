import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './MonthlyDescriptionChart.css';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';


const MonthlyDescriptionChart: React.FC = () => {
  const [counts, setCounts] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCounts = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get('/api/descriptions/monthly-counts');
        setCounts(res.data);
      } catch (err) {
        setError('Failed to load monthly description counts.');
      } finally {
        setLoading(false);
      }
    };
    fetchCounts();
  }, []);

  const validCounts = Array.isArray(counts) ? counts.filter(c => typeof c === 'number' && c >= 0) : [];
  const data = validCounts.map((count, idx) => ({ day: idx + 1, count }));

  return (
    <div className="monthly-description-chart">
      <h2 className="monthly-description-title">Monthly Description Counts</h2>
      {error && <div className="dashboard-error">{error}</div>}
      {loading ? (
        <div className="dashboard-loader" />
      ) : data.length === 0 ? (
        <div className="empty-state">
          <p>No data available for this month.</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={data}
            margin={{ top: 16, right: 24, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis
              dataKey="day"
              label={{ value: 'Day', position: 'insideBottomRight', offset: 0 }}
              tick={{ fill: '#888' }}
            />
            <YAxis
              label={{ value: 'Count', angle: -90, position: 'insideLeft' }}
              allowDecimals={false}
              tick={{ fill: '#888' }}
            />
            <Tooltip
              contentStyle={{ background: '#fff', borderRadius: 8, border: '1px solid #eee' }}
              labelStyle={{ color: '#8884d8', fontWeight: 600 }}
              itemStyle={{ color: '#222' }}
            />
            <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ color: '#8884d8' }} />
            <Line
              type="monotone"
              dataKey="count"
              name="Descriptions"
              stroke="#8884d8"
              strokeWidth={3}
              dot={{ r: 5, fill: '#fff', stroke: '#8884d8', strokeWidth: 2 }}
              activeDot={{ r: 7, fill: '#8884d8', stroke: '#fff', strokeWidth: 2 }}
              isAnimationActive={true}
              animationDuration={800}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default MonthlyDescriptionChart;
