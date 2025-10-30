import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import './RecentDescriptionsList.css';

export interface RecentDescription {
  timestamp: string;
  product_id: string;
  action: string;
  product_title?: string;
  product_image_url?: string;
}

const RecentDescriptionsList: React.FC = () => {
  const [descriptions, setDescriptions] = useState<RecentDescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDescriptions = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get('/api/descriptions/recent');
        setDescriptions(res.data);
      } catch (err) {
        setError('Failed to load recent descriptions.');
      } finally {
        setLoading(false);
      }
    };
    fetchDescriptions();
  }, []);
  // Summary: count by action
  const total = descriptions.length;
  const actionCounts = descriptions.reduce((acc, d) => {
    acc[d.action] = (acc[d.action] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Prepare data for chart: group by day and action
  const chartData: Array<{ day: string; [action: string]: number | string }> = [];
  if (descriptions.length > 0) {
    const grouped: Record<string, Record<string, number>> = {};
    (descriptions || []).forEach(desc => {
      const day = new Date(desc.timestamp).toLocaleDateString();
      if (!grouped[day]) grouped[day] = {};
      grouped[day][desc.action] = (grouped[day][desc.action] || 0) + 1;
    });
    Object.entries(grouped).forEach(([day, actions]) => {
      chartData.push({ day, ...actions });
    });
  }
  return (
    <div className="recent-descriptions-list">
      <h2 className="recent-descriptions-title">Recent Descriptions</h2>
      {error && <div className="dashboard-error">{error}</div>}
      <div className="recent-descriptions-summary">
        <span><strong>Total:</strong> {total}</span>
        {Object.entries(actionCounts).map(([action, count]) => (
          <span key={action}><strong>{action}:</strong> {count}</span>
        ))}
      </div>
      {loading ? (
        <div className="dashboard-loader" />
      ) : descriptions.length === 0 ? (
        <div className="empty-state">
          <p>No recent descriptions found.</p>
        </div>
      ) : (
        <>
          <div className="recent-descriptions-chart-container">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ top: 8, right: 24, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis dataKey="day" tick={{ fill: '#888' }} />
                <YAxis allowDecimals={false} tick={{ fill: '#888' }} />
                <Tooltip contentStyle={{ background: '#fff', borderRadius: 8, border: '1px solid #eee' }} />
                <Legend verticalAlign="top" height={32} iconType="circle" />
                {Object.keys(actionCounts).map((action, idx) => (
                  <Bar key={action} dataKey={action} name={action} fill={idx === 0 ? '#8884d8' : '#82ca9d'} radius={[4, 4, 0, 0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
          <table className="recent-descriptions-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Product</th>
                <th>Timestamp</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {descriptions.map((desc, idx) => (
                <tr key={idx} className={`recent-description-item${idx === 0 ? ' recent-description-item--highlight' : ''}`}>
                  <td>{idx + 1}</td>
                  <td className="recent-description-td-flex">
                    {desc.product_image_url ? (
                      <img src={desc.product_image_url} alt={desc.product_title || desc.product_id} className="recent-description-img" />
                    ) : (
                      <span className="recent-description-img recent-description-img--placeholder">🛒</span>
                    )}
                    <span>{desc.product_title || desc.product_id}</span>
                  </td>
                  <td>{new Date(desc.timestamp).toLocaleString()}</td>
                  <td>{desc.action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
};

export default RecentDescriptionsList;


