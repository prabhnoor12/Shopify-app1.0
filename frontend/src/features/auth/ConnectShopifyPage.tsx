
import React, { useState, useRef } from 'react';
import { Card, TextField, Button, Banner, Page, Layout, Text, Spinner } from '@shopify/polaris';
// import { useNavigate } from 'react-router-dom';
import { startShopifyAuth } from '../../api/authApi';
import './ConnectShopifyPage.css';

const ConnectShopifyPage: React.FC = () => {
  // No dev prefill in production
  const [shop, setShop] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounce submit

  const normalizeShopDomain = (input: string) => {
    let trimmed = input.trim();
    if (!trimmed) return '';
    // Remove protocol if user pasted it
    trimmed = trimmed.replace(/^https?:\/\//, '');
    // Remove trailing slashes
    trimmed = trimmed.replace(/\/$/, '');
    // If only shop name, append .myshopify.com
    if (!trimmed.endsWith('.myshopify.com')) {
      trimmed = trimmed.split('.')[0] + '.myshopify.com';
    }
    return trimmed;
  };

  const handleConnect = () => {
    if (loading || submitted) return;
    setError(null);
    setSuccess(false);
    setSubmitted(true);
    // In development, bypass auth if VITE_SHOPIFY_HOST is set
    if (import.meta.env.MODE === 'development' && import.meta.env.VITE_SHOPIFY_HOST) {
      setLoading(false);
      setSuccess(true);
      setTimeout(() => window.location.href = '/', 500); // Simulate redirect
      return;
    }
    const normalizedShop = normalizeShopDomain(shop);
    if (!/^[a-zA-Z0-9-]+\.myshopify\.com$/.test(normalizedShop)) {
      setError('Please enter a valid Shopify shop domain (e.g., mystore.myshopify.com)');
      setSubmitted(false);
      inputRef.current?.focus();
      return;
    }
    setLoading(true);
    setSuccess(true);
    // Fallback: if redirect does not happen in 5s, show error
    setTimeout(() => {
      if (success) {
        setError('Redirect failed. Please check your network or contact support.');
        setLoading(false);
        setSuccess(false);
        setSubmitted(false);
      }
    }, 5000);
    startShopifyAuth(normalizedShop);
  };

  const handleRetry = () => {
    setError(null);
    setSubmitted(false);
    setSuccess(false);
    setLoading(false);
    inputRef.current?.focus();
  };

  return (
    <div className="connect-shopify-root">
      <Page title="Connect your Shopify Store">
        <Layout>
          <Layout.Section>
            {/* No dev banner in production */}
            <Card>
              <div className="connect-header">
                <span className="connect-store-emoji" role="img" aria-label="store">🏬</span>
                <Text variant="headingMd" as="h2">
                  Connect your Shopify Store
                </Text>
              </div>
              <p className="connect-desc">
                Enter your Shopify shop domain to begin the authentication process.<br/>
                <span className="connect-hint">Example: <b>mystore.myshopify.com</b></span>
              </p>
              {error && (
                <Banner tone="critical" aria-live="assertive">
                  {error}
                  <div className="connect-retry-btn">
                    <Button onClick={handleRetry} size="slim">
                      Retry
                    </Button>
                  </div>
                </Banner>
              )}
              {success && <Banner tone="success" aria-live="polite">Redirecting to Shopify for authentication...</Banner>}
              <TextField
                label="Shop Domain"
                value={shop}
                onChange={setShop}
                placeholder="mystore.myshopify.com"
                autoComplete="off"
                helpText="You can find this in your Shopify admin URL."
                disabled={loading || success}
                aria-label="Shop Domain"
                onFocus={() => setError(null)}
              />
              <Button onClick={handleConnect} loading={loading} fullWidth disabled={loading || success || submitted} aria-label="Connect Store">
                {loading ? 'Connecting...' : 'Connect Store'}
              </Button>
              <div className="connect-shopify-actions">
                <Button
                  url="https://admin.shopify.com/oauth/install_custom_app?client_id=16d7c28b7b7d365a5b358638b9801f37&no_redirect=true&signature=eyJleHBpcmVzX2F0IjoxNzYwOTUyMDk4LCJwZXJtYW5lbnRfZG9tYWluIjoic2FuYWN1dC5teXNob3BpZnkuY29tIiwiY2xpZW50X2lkIjoiMTZkN2MyOGI3YjdkMzY1YTViMzU4NjM4Yjk4MDFmMzciLCJwdXJwb3NlIjoiY3VzdG9tX2FwcCIsIm1lcmNoYW50X29yZ2FuaXphdGlvbl9pZCI6MTc2MDcxNzkwfQ%3D%3D--cf340215fb25b4c64e6025bee969519b3ec5f21e"
                  external
                  fullWidth
                  aria-label="Install Custom App"
                >
                  Install this app on your store
                </Button>
                <div className="connect-shopify-url">
                  <span className="connect-shopify-url-text">
                    https://admin.shopify.com/oauth/install_custom_app?client_id=16d7c28b7b7d365a5b358638b9801f37&no_redirect=true&signature=eyJleHBpcmVzX2F0IjoxNzYwOTUyMDk4LCJwZXJtYW5lbnRfZG9tYWluIjoic2FuYWN1dC5teXNob3BpZnkuY29tIiwiY2xpZW50X2lkIjoiMTZkN2MyOGI3YjdkMzY1YTViMzU4NjM4Yjk4MDFmMzciLCJwdXJwb3NlIjoiY3VzdG9tX2FwcCIsIm1lcmNoYW50X29yZ2FuaXphdGlvbl9pZCI6MTc2MDcxNzkwfQ%3D%3D--cf340215fb25b4c64e6025bee969519b3ec5f21e
                  </span>
                </div>
              </div>
              {loading && (
                <div className="connect-spinner" aria-live="polite">
                  <Spinner accessibilityLabel="Connecting to Shopify" size="large" />
                </div>
              )}
            </Card>
          </Layout.Section>
        </Layout>
      </Page>
    </div>
  );
};

export default ConnectShopifyPage;
