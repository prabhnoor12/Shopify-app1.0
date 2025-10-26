import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './reactQueryClient';
import { AuthProvider, useAuth } from './authContext';
import ErrorBoundary from './components/ErrorBoundary';
import Sidebar from './components/Sidebar';
import { userApi } from './api/userApi';

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
import SubscriptionRouter from './features/subscription/subscriptionRouter';

import './App.css';

interface UserStatus {
  plan: string;
  trial_ends_at: string | null;
  generations_used: number;
  monthly_generation_limit: number;
}

// Component for protected routes that require authentication and subscription
const ProtectedRoutes: React.FC = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [subscriptionLoading, setSubscriptionLoading] = useState(true);
  const [hasValidSubscription, setHasValidSubscription] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const checkSubscription = async () => {
      // Bypass subscription checks in development
      if (import.meta.env.MODE === 'development') {
        setHasValidSubscription(true);
        setSubscriptionLoading(false);
        return;
      }

      try {
        const status: UserStatus = await userApi.getStatus();
        // Consider subscription valid if plan is not 'free' or trial is active
        const hasActivePlan = status.plan && status.plan !== 'free';
        const hasActiveTrial = status.trial_ends_at && new Date(status.trial_ends_at) > new Date();
        const isValid = hasActivePlan || hasActiveTrial;
        setHasValidSubscription(!!isValid);
      } catch (error) {
        console.error('Failed to check subscription:', error);
        setHasValidSubscription(false);
      } finally {
        setSubscriptionLoading(false);
      }
    };

    if (isAuthenticated) {
      checkSubscription();
    } else {
      setSubscriptionLoading(false);
    }
  }, [isAuthenticated]);

  // Show loading while checking auth or subscription
  if (authLoading || subscriptionLoading) {
    return (
      <div className="app-loading">
        <div className="app-loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/subscription" replace />;
  }

  // Redirect to subscription page if no valid subscription
  if (!hasValidSubscription) {
    return <Navigate to="/subscription" replace />;
  }

  // Render protected app with sidebar
  return (
    <div className="app-layout">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

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
            {/* Redirect root to dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            {/* Catch all for protected routes */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

// Main App component
const AppContent: React.FC = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/subscription/*" element={<SubscriptionRouter />} />

      {/* Protected routes */}
      <Route path="/*" element={<ProtectedRoutes />} />
    </Routes>
  );
};

// Root App component
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <div className="app">
            <AppContent />
          </div>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
