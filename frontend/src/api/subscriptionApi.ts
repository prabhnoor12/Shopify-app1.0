// Types for subscription API
export type Plan = {
  id: number;
  name: string;
  price: number;
  description?: string;
  features?: string[];
};

export interface SubscriptionInfo {
  id?: number;
  status: string;
  plan: string;
  plan_name?: string;
  trial_ends_at?: string;
  current_billing_period_starts_at?: string;
  current_billing_period_ends_at?: string;
  confirmation_url?: string;
}

// Fetch available plans from backend (TODO: implement in backend if needed)
export async function fetchPlans(): Promise<Plan[]> {
  // No /plans endpoint in backend subscription.py, so return static plans for now
  return [
    { id: 1, name: 'Basic', price: 10, description: 'Basic plan', features: ['Up to 100 orders/month', 'Basic analytics'] },
    { id: 2, name: 'Pro', price: 29, description: 'Pro plan', features: ['Up to 1000 orders/month', 'Advanced analytics', 'Priority support'] },
    { id: 3, name: 'Enterprise', price: 99, description: 'Enterprise plan', features: ['Unlimited orders', 'Custom integrations', 'Dedicated support'] },
  ];
}

// Fetch subscription status from backend
export async function fetchSubscriptionStatus(userId: number): Promise<SubscriptionInfo> {
  const res = await fetch(`/api/subscriptions/status/${userId}`);
  if (!res.ok) throw new Error('Failed to fetch subscription status');
  return res.json();
}

// Create a new subscription (POST /subscriptions)
export async function createSubscription(subscription: {
  user_id: number;
  plan_id: number;
}, shopDomain: string, accessToken: string): Promise<{ confirmation_url: string }> {
  const res = await fetch(`/api/subscriptions?shop_domain=${shopDomain}&access_token=${accessToken}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(subscription),
  });
  if (!res.ok) throw new Error('Failed to create subscription');
  return res.json();
}

// Cancel a subscription (DELETE /subscriptions/:id)
export async function cancelSubscription(subscriptionId: number, shopDomain: string, accessToken: string): Promise<any> {
  const res = await fetch(`/api/subscriptions/${subscriptionId}?shop_domain=${shopDomain}&access_token=${accessToken}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to cancel subscription');
  return res.json();
}
