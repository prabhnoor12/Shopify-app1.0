import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import './SubscriptionStatus.css';
import type { SubscriptionInfo } from '../../../api/subscriptionApi';
import { fetchSubscriptionStatus, cancelSubscription } from '../../../api/subscriptionApi';

interface SubscriptionStatusProps {
  userId: number;
  shopDomain: string;
  accessToken: string;
}

const SubscriptionStatus: React.FC<SubscriptionStatusProps> = ({ userId, shopDomain, accessToken }) => {
  const { data, isLoading, isError, error, refetch } = useQuery<SubscriptionInfo>({
    queryKey: ['subscription-status', userId],
    queryFn: () => fetchSubscriptionStatus(userId),
  });

  const cancelMutation = useMutation({
    mutationFn: ({ subscriptionId }: { subscriptionId: number }) => cancelSubscription(subscriptionId, shopDomain, accessToken),
    onSuccess: () => refetch(),
  });

  if (isLoading) return <div>Loading subscription status...</div>;
  if (isError) return <div className="error">{error instanceof Error ? error.message : 'Error loading status'}</div>;
  if (!data) return <div>No subscription info found.</div>;

  // All data is fetched internally, nothing from parent except identifiers
  const statusBadge = (status: string) => {
    let badgeClass = 'badge-default';
    if (status === 'active') badgeClass = 'badge-active';
    else if (status === 'pending') badgeClass = 'badge-pending';
    else if (status === 'canceled') badgeClass = 'badge-canceled';
    return <span className={`subscription-status-badge ${badgeClass}`}>{status}</span>;
  };

  return (
    <div className="subscription-status">
      <h2>Subscription Status</h2>
      {data && (
        <>
          <div>Status: <strong>{data.status}</strong> {statusBadge(data.status)}</div>
          <div>Plan: <strong>{data.plan_name || data.plan}</strong></div>
          {data.trial_ends_at && <div>Trial ends: {new Date(data.trial_ends_at).toLocaleDateString()}</div>}
          {data.current_billing_period_starts_at && <div>Billing period starts: {new Date(data.current_billing_period_starts_at).toLocaleDateString()}</div>}
          {data.current_billing_period_ends_at && <div>Billing period ends: {new Date(data.current_billing_period_ends_at).toLocaleDateString()}</div>}
          {data.confirmation_url && (
            <div>
              <a href={data.confirmation_url} target="_blank" rel="noopener noreferrer">Complete Subscription Setup</a>
            </div>
          )}
          {data.status === 'active' && data.id && (
            <button
              onClick={() => data.id !== undefined && cancelMutation.mutate({ subscriptionId: data.id })}
              disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending ? 'Canceling...' : 'Cancel Subscription'}
            </button>
          )}
        </>
      )}
      {cancelMutation.isError && <div className="error">{cancelMutation.error instanceof Error ? cancelMutation.error.message : 'Error canceling subscription'}</div>}
      {cancelMutation.isSuccess && <div className="success">Subscription canceled.</div>}
    </div>
  );
};

export default SubscriptionStatus;
