import React, { createContext, useContext, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { userApi } from './api/userApi';
import { fetchCurrentUser } from './api/userApi';

interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType>({ isAuthenticated: false, loading: true, error: null });

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const location = useLocation();

  useEffect(() => {
    // Bypass authentication in development if VITE_SHOPIFY_HOST is set
    if (import.meta.env.MODE === 'development' && import.meta.env.VITE_SHOPIFY_HOST) {
      setIsAuthenticated(true);
      setLoading(false);
      setError(null);
      return;
    }
    const params = new URLSearchParams(location.search);
    const shop = params.get('shop');
    const host = params.get('host');
    const accessToken = params.get('accessToken') || params.get('access_token');

    // Always set localStorage if present in query
    if (shop) {
      localStorage.setItem('shop', shop);
    }
    if (host) {
      localStorage.setItem('host', host);
    }
    if (accessToken) {
      localStorage.setItem('accessToken', accessToken);
    }

    // Use values from localStorage if not present in query
    const effectiveShop = shop || localStorage.getItem('shop');
    const effectiveToken = accessToken || localStorage.getItem('accessToken');
    let effectiveUserId = localStorage.getItem('userId');

    if (!effectiveShop) {
      setIsAuthenticated(false);
      setLoading(false);
      setError('Missing shop parameter');
      return;
    }
    if (!effectiveToken) {
      setIsAuthenticated(false);
      setLoading(false);
      setError('Missing accessToken parameter');
      return;
    }

    setLoading(true);
    // If userId is missing, fetch and store it
    const fetchAndStoreUserId = async () => {
      try {
        const user = await fetchCurrentUser();
        if (user && user.id) {
          localStorage.setItem('userId', String(user.id));
          effectiveUserId = String(user.id);
        } else {
          setError('User ID not found in backend response');
        }
      } catch (e: any) {
        setError('Failed to fetch userId: ' + (e?.message || 'Unknown error'));
      }
    };

    userApi.getStatus()
      .then(async () => {
        if (!effectiveUserId) {
          await fetchAndStoreUserId();
        }
        // Only authenticate if all required values are present
        if (localStorage.getItem('shop') && localStorage.getItem('accessToken') && localStorage.getItem('userId')) {
          setIsAuthenticated(true);
          setError(null);
        } else {
          setIsAuthenticated(false);
          setError('Missing one or more required parameters (shop, accessToken, userId)');
        }
        setLoading(false);
      })
      .catch((err: any) => {
        setIsAuthenticated(false);
        setLoading(false);
        setError('Failed to fetch user status: ' + (err?.message || 'Unknown error'));
      });
  }, [location]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, loading, error }}>
      {children}
    </AuthContext.Provider>
  );
}
