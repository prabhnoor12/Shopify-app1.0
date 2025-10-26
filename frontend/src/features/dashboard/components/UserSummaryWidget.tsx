import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './UserSummaryWidget.css';

interface UserSummary {
  name: string;
  role: string;
  last_login: string;
  email: string;
  status?: 'active' | 'new' | 'premium' | string;
  avatar_url?: string;
}

const UserSummaryWidget: React.FC = () => {
  const [summary, setSummary] = useState<UserSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get('/api/user/summary');
        setSummary(res.data);
      } catch (err) {
        setError('Failed to load user summary.');
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  return (
    <section className="user-summary-widget" aria-label="User Summary Card">
      <header className="user-summary-header">
        <h2 className="user-summary-title">User Summary</h2>
        <div className="user-summary-actions" role="group" aria-label="Quick Actions">
          <button className="dashboard-btn user-summary-btn" aria-label="Invite User">Invite</button>
          <button className="dashboard-btn user-summary-btn" aria-label="Export Users">Export</button>
          <button className="dashboard-btn user-summary-btn" aria-label="Manage Roles">Roles</button>
        </div>
      </header>
      {error && <div className="dashboard-error">{error}</div>}
      {loading ? (
        <div className="user-summary-skeleton" aria-busy="true" aria-label="Loading user summary">
          <div className="user-summary-skeleton-avatar" />
          <div className="user-summary-skeleton-lines">
            <div className="user-summary-skeleton-line" />
            <div className="user-summary-skeleton-line" />
            <div className="user-summary-skeleton-line" />
          </div>
        </div>
      ) : !summary ? (
        <div className="empty-state" tabIndex={0} aria-live="polite">
          <p>No user summary available.</p>
        </div>
      ) : (
        <div className="user-summary-content">
          <div className="user-summary-avatar-block">
            {summary.avatar_url ? (
              <img src={summary.avatar_url} alt={summary.name} className="user-summary-avatar" />
            ) : (
              <span className="user-summary-avatar user-summary-avatar--placeholder" aria-label="User Initials">{summary.name[0]}</span>
            )}
            {summary.status && (
              <span
                className={`user-summary-badge user-summary-badge--${summary.status}`}
                aria-label={`Status: ${summary.status}`}
                tabIndex={0}
              >
                {summary.status.charAt(0).toUpperCase() + summary.status.slice(1)}
              </span>
            )}
          </div>
          <ul className="user-summary-list">
            <li className="user-summary-item"><strong>Name:</strong> {summary.name}</li>
            <li className="user-summary-item"><strong>Role:</strong> {summary.role}</li>
            <li className="user-summary-item"><strong>Email:</strong> <a href={`mailto:${summary.email}`} tabIndex={0} className="user-summary-email-link">{summary.email}</a></li>
            <li className="user-summary-item"><strong>Last Login:</strong> {new Date(summary.last_login).toLocaleString()}</li>
          </ul>
        </div>
      )}
    </section>
  );
};

export default UserSummaryWidget;
