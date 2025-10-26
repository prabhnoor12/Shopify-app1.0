import React, { useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import './PlanSelector.css';
import type { Plan } from '../../../api/subscriptionApi';
import { fetchPlans, createSubscription, fetchSubscriptionStatus } from '../../../api/subscriptionApi';

interface PlanSelectorProps {
  userId: number;
  shopDomain: string;
  accessToken: string;
}

const PlanSelector: React.FC<PlanSelectorProps> = ({ userId, shopDomain, accessToken }) => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [activePlanId, setActivePlanId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetchPlans(),
      fetchSubscriptionStatus(userId)
    ])
      .then(([plansData, statusData]) => {
        setPlans(plansData);
        setActivePlanId(statusData?.id ?? null);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load plans');
        setLoading(false);
      });
  }, [userId]);

  const mutation = useMutation({
    mutationFn: ({ planId }: { planId: number }) => createSubscription({ user_id: userId, plan_id: planId }, shopDomain, accessToken),
    onSuccess: (data) => {
      if (data.confirmation_url) {
        window.location.href = data.confirmation_url;
      }
    },
  });

  if (loading) return <div>Loading plans...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="plan-selector">
      <h2>Select a Subscription Plan</h2>
      <div className="plan-list">
        {plans.map((plan) => {
          const isActive = activePlanId === plan.id;
          return (
            <div key={plan.id} className={`plan-card${isActive ? ' active' : ''}`}>
              <h3>{plan.name} {isActive && <span className="plan-badge">Current</span>}</h3>
              <p>{plan.description}</p>
              {plan.features && (
                <ul className="plan-features">
                  {plan.features.map((f, i) => <li key={i}>{f}</li>)}
                </ul>
              )}
              <div className="plan-price">${plan.price}/month</div>
              <button
                onClick={() => mutation.mutate({ planId: plan.id })}
                disabled={mutation.isPending || isActive}
              >
                {isActive ? 'Active' : mutation.isPending ? <span className="spinner" /> : 'Choose Plan'}
              </button>
            </div>
          );
        })}
      </div>
      {mutation.isError && <div className="error">{mutation.error instanceof Error ? mutation.error.message : 'Error'}</div>}
    </div>
  );
};

export default PlanSelector;
