import React from 'react';
import PlanSelector from '../components/PlanSelector';
import SubscriptionStatus from '../components/SubscriptionStatus';





const SubscriptionPage: React.FC = () => {
  const userId = Number(localStorage.getItem('userId'));
  const shopDomain = localStorage.getItem('shop') || '';
  const accessToken = localStorage.getItem('accessToken') || '';

  return (
    <div className="subscription-page">
      <h1>Manage Your Subscription</h1>
      <SubscriptionStatus userId={userId} shopDomain={shopDomain} accessToken={accessToken} />
      <PlanSelector userId={userId} shopDomain={shopDomain} accessToken={accessToken} />
    </div>
  );
};

export default SubscriptionPage;
