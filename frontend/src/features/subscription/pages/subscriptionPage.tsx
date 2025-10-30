
import React, { useEffect, useState } from 'react';
import PlanSelector from '../components/PlanSelector';
import SubscriptionStatus from '../components/SubscriptionStatus';
import './subscriptionPage.css';

const SubscriptionPage: React.FC = () => {
  const [userId, setUserId] = useState<number | null>(null);
  const [shopDomain, setShopDomain] = useState<string>('');
  const [accessToken, setAccessToken] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      // Always set values from URL if present
      const params = new URLSearchParams(window.location.search);
      const urlUserId = params.get('userId');
      const urlShop = params.get('shop');
      const urlAccessToken = params.get('accessToken');

      if (urlUserId) localStorage.setItem('userId', urlUserId);
      if (urlShop) localStorage.setItem('shop', urlShop);
      if (urlAccessToken) localStorage.setItem('accessToken', urlAccessToken);

      const storedUserId = localStorage.getItem('userId');
      const storedShop = localStorage.getItem('shop');
      const storedAccessToken = localStorage.getItem('accessToken');

      // Type validation
      if (typeof storedUserId !== 'string' || typeof storedShop !== 'string' || typeof storedAccessToken !== 'string') {
        setError('User information type mismatch. Please log in again.');
        setLoading(false);
        return;
      }

      const parsedUserId = parseInt(storedUserId, 10);
      if (isNaN(parsedUserId) || parsedUserId <= 0) {
        setError('Invalid user ID type or value. Please log in again.');
        setLoading(false);
        return;
      }

      if (!storedShop.trim()) {
        setError('Invalid shop domain. Please log in again.');
        setLoading(false);
        return;
      }

      if (!storedAccessToken.trim()) {
        setError('Invalid access token. Please log in again.');
        setLoading(false);
        return;
      }

      setUserId(parsedUserId);
      setShopDomain(storedShop);
      setAccessToken(storedAccessToken);
      setLoading(false);
    } catch (e) {
      setError('Failed to load user information. Unexpected error.');
      setLoading(false);
    }
  }, []);


  if (loading) {
    return (
      <div className="subscription-page">
        <h1>Manage Your Subscription</h1>
        <div>Loading...</div>
      </div>
    );
  }

  if (error || userId === null || shopDomain === '' || accessToken === '') {
    return (
      <div className="subscription-page">
        <h1>Manage Your Subscription</h1>
        <div className="error">{error || 'Invalid user or shop information.'}</div>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
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
