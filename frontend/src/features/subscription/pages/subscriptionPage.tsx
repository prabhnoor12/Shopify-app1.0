import React from 'react';
import PlanSelector from '../components/PlanSelector';
import SubscriptionStatus from '../components/SubscriptionStatus';



// Get identifiers from localStorage or context (adjust as needed for your app)
const userId = Number(localStorage.getItem('userId'));
const shopDomain = localStorage.getItem('shop');
const accessToken = localStorage.getItem('accessToken');

const SubscriptionPage: React.FC = () => {
  if (!userId || !shopDomain || !accessToken) {
    return <div className="error">Missing authentication info. Please log in.</div>;
  }

  return (
    <div className="subscription-page">
      <h1>Manage Your Subscription</h1>
      <SubscriptionStatus userId={userId} shopDomain={shopDomain} accessToken={accessToken} />
      <PlanSelector userId={userId} shopDomain={shopDomain} accessToken={accessToken} />
    </div>
  );
};

export default SubscriptionPage;
