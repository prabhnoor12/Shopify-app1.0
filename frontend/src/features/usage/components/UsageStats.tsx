import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getUsageStats } from '../../../api/usage';
import './UsageStats.css';

const usageFields = [
  { key: 'descriptions_generated_short', label: 'Short Descriptions Generated', icon: '📝', max: 1000 },
  { key: 'descriptions_generated_long', label: 'Long Descriptions Generated', icon: '📄', max: 1000 },
  { key: 'images_processed_sd', label: 'Images Processed (SD)', icon: '🖼️', max: 500 },
  { key: 'images_processed_hd', label: 'Images Processed (HD)', icon: '🖼️', max: 500 },
  { key: 'brand_voices_created', label: 'Brand Voices Created', icon: '🎤', max: 100 },
  { key: 'brand_voice_edited', label: 'Brand Voices Edited', icon: '✏️', max: 100 },
  { key: 'analytics_reports_generated', label: 'Analytics Reports Generated', icon: '📊', max: 200 },
  { key: 'api_calls_made', label: 'API Calls Made', icon: '🔗', max: 5000 },
  { key: 'storage_used_mb', label: 'Storage Used (MB)', icon: '💾', max: 10000 },
];

const UsageStats: React.FC = () => {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['usageStats'],
    queryFn: getUsageStats,
  });

  if (isLoading) return <div>Loading usage stats...</div>;
  if (isError || !data) return <div className="usage-error">Failed to load usage stats.</div>;
  if (!data.success) return <div className="usage-error">{data.error || data.message}</div>;

  const stats = data.data || {};
  const totalUsage = usageFields.reduce((sum, field) => sum + (stats[field.key] ?? 0), 0);

  return (
    <div className="usage-stats-card">
      <h2>Usage Statistics</h2>
      <div className="usage-total">
        Total Usage: {totalUsage}
      </div>
      <ul>
        {usageFields.map(field => {
          const value = stats[field.key] ?? 0;
          const percent = Math.min(100, Math.round((value / field.max) * 100));
          return (
            <li key={field.key}>
              <span className="usage-icon" title={field.label}>{field.icon}</span>
              {field.label}: {value}
              <div className="usage-bar">
                <div className={`usage-bar-fill usage-bar-fill-${Math.round(percent / 10) * 10}`}></div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default UsageStats;
