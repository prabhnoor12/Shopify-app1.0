import React, { useState,  } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './reactQueryClient';
import { AuthProvider, useAuth } from './authContext';
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
// ...existing code...

import './App.css';

interface UserStatus {
  plan: string;
  trial_ends_at: string | null;
  generations_used: number;
  monthly_generation_limit: number;
}

// Component for protected routes that require authentication
const ProtectedRoutes: React.FC = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="app-loading">
        <div className="app-loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
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
