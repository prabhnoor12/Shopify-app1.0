// src/api/client.ts


const BASE_API_URL = 'https://shopify-app1-0.onrender.com';

const request = async (url: string, method: string, data?: any) => {
  const fullUrl = url.startsWith('http') ? url : `${BASE_API_URL}${url}`;
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(fullUrl, options);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || 'Network response was not ok');
  }

  if (response.status === 204) { // No Content
    return null;
  }

  return response.json();
};

export const client = {
  get: (url: string) => request(url, 'GET'),
  post: (url: string, data: any) => request(url, 'POST', data),
  put: (url: string, data: any) => request(url, 'PUT', data),
  patch: (url: string, data: any) => request(url, 'PATCH', data),
  delete: (url: string) => request(url, 'DELETE'),
};
