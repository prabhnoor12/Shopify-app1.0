// Handles Shopify authentication API calls

// Add a type declaration for window.env if it exists
declare global {
  interface Window {
    env?: Record<string, string>;
  }
}

/**
 * Starts the Shopify OAuth installation flow by redirecting to the backend /auth/install endpoint.
 * @param shop The shop domain (e.g., mystore.myshopify.com)
 */
export const startShopifyAuth = (shop: string): void => {
  const params = new URLSearchParams({ shop });
  const backendUrl =
    import.meta.env.VITE_BACKEND_URL ||
    window?.env?.VITE_BACKEND_URL ||
    'https://127.0.0.1:8000';
  window.location.href = `${backendUrl}/auth/install?${params.toString()}`;
};

/**
 * Optionally, handle the OAuth callback from the frontend (rare).
 * Most of the time, Shopify will redirect to your backend /auth/callback.
 * This is only needed if you want to trigger the callback manually.
 * @param params The query parameters returned by Shopify (shop, code, state, hmac, etc.)
 * @returns Promise with backend response
 */
export const triggerShopifyCallback = async (params: Record<string, string>) => {
  const backendUrl =
    import.meta.env.VITE_BACKEND_URL ||
    window?.env?.VITE_BACKEND_URL ||
    'https://127.0.0.1:8000';
  const url = new URL(`${backendUrl}/auth/callback`);
  (Object.entries(params) || []).forEach(([key, value]) => url.searchParams.append(key, value));
  const response = await fetch(url.toString(), {
    method: 'GET',
    credentials: 'include',
  });
  return response;
};


