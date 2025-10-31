import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './TeamActivityWidget.css';

interface TeamActivity {
  // Update with real fields when backend is ready
  id: number;
  user: string;
  action: string;
  timestamp: string;
}

const TeamActivityWidget: React.FC = () => {
  const [activity, setActivity] = useState<TeamActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchActivity = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get('/api/team/activity');
        setActivity(res.data);
      } catch (err) {
        setError('Failed to load team activity.');
      } finally {
        setLoading(false);
      }
    };
    fetchActivity();
  }, []);

  return (
    <div className="team-activity-widget">
      <h2 className="team-activity-title">Team Activity</h2>
      {error && <div className="dashboard-error">{error}</div>}
      {loading ? (
        <div className="dashboard-loader" />
      ) : (!Array.isArray(activity) || activity.length === 0) ? (
        <div className="empty-state">
          <p>No team activity data available.</p>
        </div>
      ) : (
        <ul className="team-activity-list">
          {Array.isArray(activity) && activity.map((item) => (
            <li key={item.id} className="team-activity-item">
              <span className="team-activity-user">{item.user}</span> {item.action}
              <span className="team-activity-timestamp">{new Date(item.timestamp).toLocaleString()}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TeamActivityWidget;
