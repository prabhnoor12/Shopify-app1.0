
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
      // Read from URL first
      const params = new URLSearchParams(window.location.search);
      const urlUserId = params.get('userId');
      const urlShop = params.get('shop');
      const urlAccessToken = params.get('accessToken');

      // Store in localStorage if present in URL
      if (urlUserId) localStorage.setItem('userId', urlUserId);
      if (urlShop) localStorage.setItem('shop', urlShop);
      if (urlAccessToken) localStorage.setItem('accessToken', urlAccessToken);

      // Always read from localStorage after possible update
      const storedUserIdRaw = localStorage.getItem('userId');
      const storedShopRaw = localStorage.getItem('shop');
      const storedAccessTokenRaw = localStorage.getItem('accessToken');

      // Debug info for troubleshooting
      // console.log('SubscriptionPage values:', { urlUserId, urlShop, urlAccessToken, storedUserIdRaw, storedShopRaw, storedAccessTokenRaw });

      // Validate presence
      let missingFields: string[] = [];
      if (!storedUserIdRaw) missingFields.push('User ID');
      if (!storedShopRaw) missingFields.push('Shop Domain');
      if (!storedAccessTokenRaw) missingFields.push('Access Token');
      if (missingFields.length > 0) {
        setError(`Missing user information: ${missingFields.join(', ')}. Please log in again.`);
        setLoading(false);
        return;
      }

      // Validate types and values
      const parsedUserId = parseInt(storedUserIdRaw ?? '', 10);
      if (isNaN(parsedUserId) || parsedUserId <= 0) {
        setError('Invalid user ID type or value. Please log in again.');
        setLoading(false);
        return;
      }
      if ((storedShopRaw ?? '').trim() === '') {
        setError('Invalid shop domain. Please log in again.');
        setLoading(false);
        return;
      }
      if ((storedAccessTokenRaw ?? '').trim() === '') {
        setError('Invalid access token. Please log in again.');
        setLoading(false);
        return;
      }

      // Store in state
      setUserId(parsedUserId);
      setShopDomain(storedShopRaw ?? '');
      setAccessToken(storedAccessTokenRaw ?? '');
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
