import './TeamPerformance.css';
import './AnalyticsCard.css';
import React, { memo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export interface TeamMemberPerformance {
  user_id: number;
  user_name: string;
  descriptions_generated: number;
  descriptions_published: number;
  products_managed: number;
  average_conversion_rate: number;
}

interface TeamPerformanceProps {
  members: TeamMemberPerformance[];
  loading?: boolean;
  error?: string | null;
}

const TeamPerformance: React.FC<TeamPerformanceProps> = memo(({ members, loading = false, error = null }) => {
  if (loading) {
    return (
      <div className="team-performance analytics-card" role="status" aria-busy="true">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#8884d8" strokeWidth="2" opacity="0.3"/><path d="M12 2a10 10 0 0 1 10 10" stroke="#8884d8" strokeWidth="2"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/></path></svg>
          Loading team performance...
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="team-performance analytics-card" role="alert">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#ff4d4f" strokeWidth="2" opacity="0.3"/><path d="M12 8v4m0 4h.01" stroke="#ff4d4f" strokeWidth="2" strokeLinecap="round"/></svg>
          {error}
        </div>
      </div>
    );
  }
  if (!members || members.length === 0) {
    return (
      <div className="team-performance analytics-card" role="status">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#888" strokeWidth="2" opacity="0.2"/><path d="M8 12h8M12 8v8" stroke="#888" strokeWidth="2" strokeLinecap="round"/></svg>
          No team performance data available.
        </div>
      </div>
    );
  }
  return (
    <div className="team-performance analytics-card">
      <h2 className="analytics-card-title">Team Performance</h2>
      <div className="team-performance-chart-container analytics-card-section" aria-label="Team performance chart">
        <ResponsiveContainer>
          <BarChart data={members} margin={{ top: 30, right: 40, left: 40, bottom: 30 }}>
            <XAxis
              dataKey="user_name"
              label={{ value: 'User', position: 'insideBottom', offset: 14, style: { textAnchor: 'middle', fontSize: 15, fontWeight: 500 } }}
              tick={{ fontSize: 13, dy: 8 }}
              interval={0}
              padding={{ left: 8, right: 8 }}
            />
            <YAxis
              label={{ value: 'Count', angle: -90, position: 'insideLeft', offset: 18, style: { textAnchor: 'middle', fontSize: 15, fontWeight: 500, fill: '#23272f' } }}
              tick={{ fontSize: 13, dx: -8, fill: '#23272f' }}
              axisLine={{ stroke: '#bdbdbd', strokeWidth: 2 }}
              tickLine={{ stroke: '#bdbdbd', strokeWidth: 1 }}
            />
            <Tooltip />
            <Legend wrapperStyle={{ paddingTop: 10 }} />
            <Bar dataKey="descriptions_generated" fill="#8884d8" name="Descriptions Generated" />
            <Bar dataKey="descriptions_published" fill="#82ca9d" name="Descriptions Published" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="team-performance-table-wrapper analytics-card-section">
        <table className="team-performance-table" aria-label="Team performance table">
          <thead>
            <tr>
              <th>User</th>
              <th>Descriptions Generated</th>
              <th>Descriptions Published</th>
              <th>Products Managed</th>
              <th>Avg. Conversion Rate (%)</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.user_id}>
                <td>{m.user_name}</td>
                <td>{m.descriptions_generated}</td>
                <td>{m.descriptions_published}</td>
                <td>{m.products_managed}</td>
                <td>{m.average_conversion_rate.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
});

export default TeamPerformance;
