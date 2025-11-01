import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './reactQueryClient';

import ErrorBoundary from './components/ErrorBoundary';
import Sidebar from './components/Sidebar';


// Import all feature routers
import DashboardRouter from './features/dashboard/DashboardRouter';
import AnalyticsRouter from './features/analytics/AnalyticsRouter';
import ProductRouter from './features/product/ProductRouter';
import SeoRouter from './features/seo/SeoRouter';
import ABTestingRouter from './features/ab-testing/ABTestingRouter';
import TeamRouter from './features/team/TeamRouter';
import UsageRouter from './features/usage/UsageRouter';
import ShopRouter from './features/shop/ShopRouter';
import UserRouter from './features/user/UserRouter';

import './App.css';
import { CookieBanner, PrivacyPolicy } from './features/privacy/components';

const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Parse URL params for user info and store in localStorage
  useEffect(() => {
    // Improved: parse both search and hash fragments for params
    const getParams = () => {
      let params = new URLSearchParams(window.location.search);
      // If not found, try hash fragment (for some OAuth flows)
      if (!params.has('shop') || !(params.has('user_id') || params.has('userId')) || !(params.has('access_token') || params.has('accessToken'))) {
        if (window.location.hash) {
          const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, '?'));
          params = hashParams;
        }
      }
      // Collect all keys and values from the backend URL
      const allKeys = Array.from(params.keys());
      const allValues: Record<string, string | null> = {};
      allKeys.forEach((key: string) => {
        allValues[key] = params.get(key);
      });
      // Expected keys
      const expectedKeys = ['shop', 'user_id', 'access_token'];
      const altKeys = ['userId', 'accessToken'];
      // Find missing and mismatched keys
      const missingKeys = expectedKeys.filter(k => !params.has(k) && !(altKeys.includes(k)));
      const mismatchedKeys = allKeys.filter(k => !expectedKeys.includes(k) && !altKeys.includes(k));
      return {
        shop: params.get('shop'),
        user_id: params.get('user_id') || params.get('userId'),
        access_token: params.get('access_token') || params.get('accessToken'),
        allKeys,
        allValues,
        missingKeys,
        mismatchedKeys
      };
    };

    const { shop, user_id, access_token, allKeys, allValues, missingKeys, mismatchedKeys } = getParams();

    // Enhanced debug logging
    console.group('[Auth Debug] Step 1: URL Parameter Parsing');
    console.log('window.location.search:', window.location.search);
    console.log('window.location.hash:', window.location.hash);
    console.log('All keys from backend URL:', allKeys);
    console.log('All values from backend URL:', allValues);
    console.log('Parsed (used) values:', { shop, user_id, access_token });
    if (missingKeys.length > 0) {
      console.warn('Missing expected keys:', missingKeys);
    }
    if (mismatchedKeys.length > 0) {
      console.warn('Unexpected/mismatched keys in URL:', mismatchedKeys);
    }
    if (!shop) {
      console.warn('Missing "shop" param. Backend should send ?shop=SHOP_DOMAIN');
    }
    if (!user_id) {
      console.warn('Missing "user_id"/"userId" param. Backend should send ?userId=USER_ID');
    }
    if (!access_token) {
      console.warn('Missing "access_token"/"accessToken" param. Backend should send ?accessToken=TOKEN');
    }
    if (typeof shop !== 'string' || typeof user_id !== 'string' || typeof access_token !== 'string') {
      console.error('One or more params are not strings:', { shop, user_id, access_token });
    }
    console.groupEnd();

    if (shop && user_id && access_token) {
      localStorage.setItem('shop', shop);
      localStorage.setItem('user_id', user_id);
      localStorage.setItem('access_token', access_token);
      window.history.replaceState({}, document.title, window.location.pathname);
      console.group('[Auth Debug] Step 2: Saved to localStorage');
      console.log('Auth info saved:', { shop, user_id, access_token });
      console.groupEnd();
    } else {
      console.group('[Auth Debug] Step 2: Save to localStorage FAILED');
      console.warn('Auth info NOT saved. Check previous warnings for missing values.');
      console.groupEnd();
    }
  }, []);

  // Retrieve from localStorage for authentication/backend usage
  const shop = localStorage.getItem('shop');
  const userId = localStorage.getItem('user_id');
  const accessToken = localStorage.getItem('access_token');
  // Enhanced debug log for localStorage
  console.group('[Auth Debug] Step 3: LocalStorage Retrieval');
  console.log('LocalStorage values:', { shop, userId, accessToken });
  if (!shop || !userId || !accessToken) {
    console.warn('LocalStorage missing auth info. Possible causes:');
    console.warn('- OAuth redirect did not include all required params');
    console.warn('- localStorage was cleared or blocked');
    console.warn('- URL param names do not match expected keys');
    console.warn('Check backend redirect and browser privacy settings.');
  }
  console.groupEnd();

  return (
    <div className="app-layout">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <CookieBanner />
      <div className="app-main">
        {/* Mobile menu button - only show when sidebar is closed */}
        {!sidebarOpen && (
          <button
            className="mobile-menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            ☰
          </button>
        )}
        <div className="app-content">
          {/* Show user info if available */}
          {shop && userId && accessToken ? (
            <div style={{ marginBottom: '1rem', background: '#f6f6f6', padding: '0.5rem', borderRadius: '4px' }}>
              <strong>Authenticated as:</strong> {shop}<br />
              <strong>User ID:</strong> {userId}
            </div>
          ) : (
            <div style={{ marginBottom: '1rem', color: 'red' }}>Not authenticated</div>
          )}
          <Routes>
            <Route path="/dashboard/*" element={<DashboardRouter />} />
            <Route path="/analytics/*" element={<AnalyticsRouter />} />
            <Route path="/products/*" element={<ProductRouter />} />
            <Route path="/seo/*" element={<SeoRouter />} />
            <Route path="/ab-testing/*" element={<ABTestingRouter />} />
            <Route path="/team/*" element={<TeamRouter />} />
            <Route path="/usage/*" element={<UsageRouter />} />
            <Route path="/shop/*" element={<ShopRouter />} />
            <Route path="/user/*" element={<UserRouter />} />
            <Route path="/privacy-policy" element={<PrivacyPolicy />} />
            <Route path="*" element={<DashboardRouter />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}


const AppContent: React.FC = () => {
  return (
    <Routes>
      <Route path="/*" element={<AppLayout />} />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <div className="app">
          <AppContent />
        </div>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
