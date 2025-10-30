import React, { createContext, useContext, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { userApi } from './api/userApi';
import { fetchCurrentUser } from './api/userApi';


interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  userId?: string | null;
  shop?: string | null;
  accessToken?: string | null;
  login: (shop: string, accessToken: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}


const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  loading: true,
  error: null,
  userId: null,
  shop: null,
  accessToken: null,
  login: async () => {},
  logout: () => {},
  refreshUser: async () => {},
});


export function useAuth() {
  return useContext(AuthContext);
}


export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [shop, setShop] = useState<string | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const location = useLocation();

  // Helper: logout and clear all auth data
  const logout = () => {
    setIsAuthenticated(false);
    setUserId(null);
    setShop(null);
    setAccessToken(null);
    setError(null);
    setLoading(false);
    localStorage.removeItem('shop');
    localStorage.removeItem('host');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('userId');
  };

  // Helper: login and store auth data
  const login = async (shopParam: string, accessTokenParam: string) => {
    setLoading(true);
    setError(null);
    try {
      localStorage.setItem('shop', shopParam);
      localStorage.setItem('accessToken', accessTokenParam);
      setShop(shopParam);
      setAccessToken(accessTokenParam);
      // Fetch userId
      const user = await fetchCurrentUser();
      if (user && user.id) {
        localStorage.setItem('userId', String(user.id));
        setUserId(String(user.id));
        setIsAuthenticated(true);
      } else {
        throw new Error('User ID not found in backend response');
      }
    } catch (e: any) {
      setIsAuthenticated(false);
      setError('Login failed: ' + (e?.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  // Helper: refresh user info
  const refreshUser = async () => {
    setLoading(true);
    setError(null);
    try {
      const user = await fetchCurrentUser();
      if (user && user.id) {
        localStorage.setItem('userId', String(user.id));
        setUserId(String(user.id));
      } else {
        throw new Error('User ID not found in backend response');
      }
    } catch (e: any) {
      setError('Failed to refresh user: ' + (e?.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

 

  useEffect(() => {
    // Bypass authentication in development if VITE_SHOPIFY_HOST is set
    if (import.meta.env.MODE === 'development' && import.meta.env.VITE_SHOPIFY_HOST) {
      setIsAuthenticated(true);
      setLoading(false);
      setError(null);
      setShop(import.meta.env.VITE_SHOPIFY_HOST);
      return;
    }
    const params = new URLSearchParams(location.search);
    const shopParam = params.get('shop');
    const hostParam = params.get('host');
    const accessTokenParam = params.get('accessToken') || params.get('access_token');

    // Always set localStorage if present in query
    if (shopParam) {
      localStorage.setItem('shop', shopParam);
      setShop(shopParam);
    } else {
      setShop(localStorage.getItem('shop'));
    }
    if (hostParam) {
      localStorage.setItem('host', hostParam);
    }
    if (accessTokenParam) {
      localStorage.setItem('accessToken', accessTokenParam);
      setAccessToken(accessTokenParam);
    } else {
      setAccessToken(localStorage.getItem('accessToken'));
    }

    // Use values from localStorage if not present in query
    const effectiveShop = shopParam || localStorage.getItem('shop');
    const effectiveToken = accessTokenParam || localStorage.getItem('accessToken');
    let effectiveUserId = localStorage.getItem('userId');


    // Robust fallback for missing shop/accessToken
    if (!effectiveShop) {
      logout();
      const missingFromLocalStorage = !localStorage.getItem('shop');
      const missingFromUrl = !shopParam;
      let details = 'Missing shop parameter.';
      details += '\nSource:';
      if (missingFromLocalStorage && missingFromUrl) {
        details += ' Not found in localStorage or URL.';
      } else if (missingFromLocalStorage) {
        details += ' Not found in localStorage.';
      } else if (missingFromUrl) {
        details += ' Not found in URL.';
      }
      details += '\nPlease re-authenticate via Shopify.';
      setError(details);
      // Optionally, redirect to install/auth flow:
      // window.location.href = `/api/auth/install`;
      return;
    }
    if (!effectiveToken) {
      logout();
      const missingFromLocalStorage = !localStorage.getItem('accessToken');
      const missingFromUrl = !(accessTokenParam);
      let details = 'Missing accessToken parameter.';
      details += '\nSource:';
      if (missingFromLocalStorage && missingFromUrl) {
        details += ' Not found in localStorage or URL.';
      } else if (missingFromLocalStorage) {
        details += ' Not found in localStorage.';
      } else if (missingFromUrl) {
        details += ' Not found in URL.';
      }
      details += '\nPlease re-authenticate via Shopify.';
      setError(details);
      // Optionally, redirect to install/auth flow:
      // window.location.href = `/api/auth/install`;
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
          setUserId(String(user.id));
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
        } else {
          setUserId(effectiveUserId);
        }
        // Only authenticate if all required values are present
        if (localStorage.getItem('shop') && localStorage.getItem('accessToken') && localStorage.getItem('userId')) {
          setIsAuthenticated(true);
          setError(null);
        } else {
          logout();
          setError('Missing one or more required parameters (shop, accessToken, userId)');
        }
        setLoading(false);
      })
      .catch((err: any) => {
        logout();
        setError('Failed to fetch user status: ' + (err?.message || 'Unknown error'));
      });
  }, [location]);

  // Memoize context value for performance
  const contextValue = React.useMemo(() => ({
    isAuthenticated,
    loading,
    error,
    userId,
    shop,
    accessToken,
    login,
    logout,
    refreshUser,
  }), [isAuthenticated, loading, error, userId, shop, accessToken]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}
