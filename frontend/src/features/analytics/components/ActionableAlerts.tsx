import './ActionableAlerts.css';
import React, { memo } from 'react';
import { Banner } from '@shopify/polaris';

export interface ActionableAlert {
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  status?: 'critical' | 'warning' | 'info' | 'success';
}

interface ActionableAlertsProps {
  alerts: ActionableAlert[];
  loading?: boolean;
  error?: string | null;
}

const ActionableAlerts: React.FC<ActionableAlertsProps> = memo(({ alerts, loading = false, error = null }) => {
  return (
    <section className="actionable-alerts" aria-label="Actionable Alerts">
      <h2 className="actionable-alerts-title">Actionable Alerts</h2>
      {loading ? (
        <Banner tone="info" title="Loading alerts..." />
      ) : error ? (
        <Banner tone="critical" title={error} />
      ) : !alerts || alerts.length === 0 ? (
        <Banner tone="info" title="No actionable alerts at this time." />
      ) : (
        <div className="actionable-alerts-list" aria-label="Actionable alerts list">
          {alerts.map((alert, idx) => (
            <Banner
              key={idx}
              tone={alert.status || 'warning'}
              title={alert.message}
              action={
                alert.actionLabel && alert.onAction
                  ? { content: alert.actionLabel, onAction: alert.onAction }
                  : undefined
              }
              hideIcon={false}
            />
          ))}
        </div>
      )}
    </section>
  );
});

export default ActionableAlerts;
