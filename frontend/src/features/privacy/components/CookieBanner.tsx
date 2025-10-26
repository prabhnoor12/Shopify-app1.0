import React, { useState, useEffect } from 'react';
import { Banner, Button, ButtonGroup, Link } from '@shopify/polaris';
import './CookieBanner.css';

const CookieBanner: React.FC = () => {
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    try {
      const consent = localStorage.getItem('cookieConsent');
      if (!consent) {
        setShowBanner(true);
      }
    } catch (error) {
      // localStorage not available, show banner
      setShowBanner(true);
    }
  }, []);

  const handleAccept = () => {
    try {
      localStorage.setItem('cookieConsent', 'accepted');
    } catch (error) {
      console.warn('Unable to store cookie consent:', error);
    }
    setShowBanner(false);
    // Enable analytics/tracking here
  };

  const handleReject = () => {
    try {
      localStorage.setItem('cookieConsent', 'rejected');
    } catch (error) {
      console.warn('Unable to store cookie consent:', error);
    }
    setShowBanner(false);
    // Disable analytics/tracking here
  };

  const handleManage = () => {
    // Open a preferences modal or redirect to settings
    alert('Cookie preferences management coming soon!');
  };

  if (!showBanner) return null;

  return (
    <div className="cookie-banner">
      <Banner tone="info" onDismiss={() => setShowBanner(false)}>
        <p>
          We use cookies to improve your experience, analyze site traffic, and personalize content. By clicking "Accept", you consent to our use of cookies.
          <br />
          <Link url="/privacy-policy">Learn more in our Privacy Policy</Link>.
        </p>
        <br />
        <ButtonGroup>
          <Button onClick={handleAccept} variant="primary">Accept</Button>
          <Button onClick={handleReject}>Reject</Button>
          <Button onClick={handleManage} variant="plain">Manage Preferences</Button>
        </ButtonGroup>
      </Banner>
    </div>
  );
};

export default CookieBanner;
