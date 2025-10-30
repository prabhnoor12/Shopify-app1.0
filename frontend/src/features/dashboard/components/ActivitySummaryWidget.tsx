import React, { useEffect, useState } from 'react';
import { Card, Text, Select,  Banner } from '@shopify/polaris';
import axios from 'axios';
import './ActivitySummaryWidget.css';

interface Activity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
}

interface SummaryStats {
  totalActions: number;
  mostFrequentType: string;
  period: string;
}

const PERIOD_OPTIONS = [
  { label: 'Last 7 days', value: '7d' },
  { label: 'Last 30 days', value: '30d' },
  { label: 'This month', value: 'month' },
  { label: 'This year', value: 'year' },
];

const ActivitySummaryWidget: React.FC = () => {
  const [period, setPeriod] = useState('7d');
  const [activities, setActivities] = useState<Activity[]>([]);
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  useEffect(() => {
    const fetchActivity = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await axios.get(`/api/activity/me?period=${period}`);
        setActivities(res.data.activities);
        setSummary(res.data.summary);
      } catch (e) {
        setError('Failed to load activity summary.');
      } finally {
        setLoading(false);
      }
    };
    fetchActivity();
  }, [period]);

  // Advanced: Get unique activity types and counts
  const typeCounts: Record<string, number> = {};
  (activities || []).forEach(act => {
    typeCounts[act.type] = (typeCounts[act.type] || 0) + 1;
  });
  const typeOptions = [
    { label: 'All types', value: '' },
    ...Object.keys(typeCounts).map(type => ({ label: `${type} (${typeCounts[type]})`, value: type }))
  ];

  // Advanced: Filter activities by type
  const filteredActivities = typeFilter ? activities.filter(a => a.type === typeFilter) : activities;

  // Advanced: Export to CSV
  const handleExportCSV = () => {
    const rows = [
      ['Type', 'Description', 'Timestamp'],
      ...filteredActivities.map(a => [a.type, a.description, a.timestamp])
    ];
    const csv = rows.map(r => r.map(x => `"${x.replace(/"/g, '""')}` ).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `activity_${period}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <div className="activity-summary-widget">
        <Text as="h2" variant="headingMd">Your Activity Summary</Text>
        <div className="activity-summary-period">
          <Select
            label="Period"
            options={PERIOD_OPTIONS}
            value={period}
            onChange={setPeriod}
          />
        </div>
        {Object.keys(typeCounts).length > 0 && (
          <div className="activity-summary-type-counts">
            <Text as="span" variant="bodySm">Type counts: {Object.entries(typeCounts).map(([type, count]) => `${type}: ${count}`).join(', ')}</Text>
          </div>
        )}
        <div className="activity-summary-filter">
          <Select
            label="Filter by type"
            options={typeOptions}
            value={typeFilter}
            onChange={setTypeFilter}
          />
        </div>
        <div className="activity-summary-export">
          <button className="dashboard-btn" onClick={handleExportCSV}>Export CSV</button>
        </div>
        {error && <Banner title="Error" tone="critical">{error}</Banner>}
        {loading ? (
          <div className="dashboard-loader" />
        ) : (
          <>
            {summary && (
              <div className="activity-summary-summary">
                <Text as="span" variant="bodyMd"><strong>Total actions:</strong> {summary.totalActions}</Text><br />
                <Text as="span" variant="bodyMd"><strong>Most frequent type:</strong> {summary.mostFrequentType}</Text><br />
                <Text as="span" variant="bodyMd"><strong>Period:</strong> {summary.period}</Text>
              </div>
            )}
            <div>
              <div className="activity-summary-heading">
                <Text as="h3" variant="headingSm">Recent Activity</Text>
              </div>
              {filteredActivities.length === 0 ? (
                <Text as="span">No activity found for this period.</Text>
              ) : (
                <ul className="activity-summary-list">
                  {filteredActivities.map(act => (
                    <li key={act.id} className="activity-summary-item">
                      <Text as="span" variant="bodySm">
                        <strong>{act.type}</strong>: {act.description} <em>({new Date(act.timestamp).toLocaleString()})</em>
                      </Text>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}
      </div>
    </Card>
  );
};

export default ActivitySummaryWidget;
