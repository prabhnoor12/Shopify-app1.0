import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
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
    const params = new URLSearchParams(window.location.search);
    const shop = params.get('shop');
    const userId = params.get('user_id');
    const accessToken = params.get('access_token');

    if (shop && userId && accessToken) {
      localStorage.setItem('shop', shop);
      localStorage.setItem('user_id', userId);
      localStorage.setItem('access_token', accessToken);
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // Retrieve from localStorage for authentication/backend usage
  const shop = localStorage.getItem('shop');
  const userId = localStorage.getItem('user_id');
  const accessToken = localStorage.getItem('access_token');

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
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
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
