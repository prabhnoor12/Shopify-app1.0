import React, { createContext, useContext, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { userApi } from './api/userApi';
import { fetchCurrentUser } from './api/userApi';

interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType>({ isAuthenticated: false, loading: true });

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    // Bypass authentication in development if VITE_SHOPIFY_HOST is set
    if (import.meta.env.MODE === 'development' && import.meta.env.VITE_SHOPIFY_HOST) {
      setIsAuthenticated(true);
      setLoading(false);
      return;
    }
    const params = new URLSearchParams(location.search);
    const shop = params.get('shop');
    const host = params.get('host');
  const accessToken = params.get('accessToken') || params.get('access_token');
    if (shop) {
      localStorage.setItem('shop', shop);
    }
    if (host) {
      localStorage.setItem('host', host);
    }
    if (accessToken) {
      localStorage.setItem('accessToken', accessToken);
    }
  const effectiveShop = shop || localStorage.getItem('shop');
  const effectiveToken = accessToken || localStorage.getItem('accessToken');
    if (!effectiveShop || !effectiveToken) {
      setIsAuthenticated(false);
      setLoading(false);
      return;
    }
    setLoading(true);
    userApi.getStatus()
      .then(async () => {
        // Fetch userId after authentication
        try {
          const user = await fetchCurrentUser();
          if (user && user.id) {
            localStorage.setItem('userId', String(user.id));
          }
        } catch (e) {
          // Optionally handle error
        }
        setIsAuthenticated(true);
        setLoading(false);
      })
      .catch(() => {
        setIsAuthenticated(false);
        setLoading(false);
      });
  }, [location]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, loading }}>
      {children}
    </AuthContext.Provider>
  );
}
