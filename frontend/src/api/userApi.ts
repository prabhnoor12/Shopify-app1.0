

let backendAvailable = true;

export const fetchCurrentUser = async () => {
  // In development, check backend availability before calling
  if (import.meta.env.MODE === 'development' && !backendAvailable) {
    throw new Error('Backend unavailable');
  }
  try {
    const response = await axios.get(`/api/users/me`);
    return response.data;
  } catch (err: any) {
    if (import.meta.env.MODE === 'development') {
      // Mark backend unavailable for network errors or 404
      if (!err.response || err.response.status === 404) {
        backendAvailable = false;
      }
    }
    throw err;
  }
};

import { client } from './client';

export interface UserStatus {
  plan: string;
  trial_ends_at: string | null;
  generations_used: number;
  monthly_generation_limit: number;
}

export const userApi = {
  getStatus: async (): Promise<UserStatus> => {
    if (import.meta.env.MODE === 'development' && !backendAvailable) {
      throw new Error('Backend unavailable');
    }
    const shop = localStorage.getItem('shop');
    const url = shop ? `/api/status?shop=${encodeURIComponent(shop)}` : '/api/status';
    try {
      return await client.get(url);
    } catch (err: any) {
      if (import.meta.env.MODE === 'development') {
        // Mark backend unavailable for network errors or 404
        if (!err.response || err.response.status === 404) {
          backendAvailable = false;
        }
      }
      throw err;
    }
  },
};

import axios from 'axios';

const BASE_URL = '/api/users';

export const fetchUsers = async () => {
  const res = await axios.get(`${BASE_URL}/`);
  return res.data;
};

export const fetchUserById = async (userId: string) => {
  const res = await axios.get(`${BASE_URL}/${userId}`);
  return res.data;
};

export const createUser = async (data: Record<string, any>) => {
  const res = await axios.post(`${BASE_URL}/`, data);
  return res.data;
};

export const updateUser = async (userId: string, data: Record<string, any>) => {
  const res = await axios.put(`${BASE_URL}/${userId}`, data);
  return res.data;
};

export const deleteUser = async (userId: string) => {
  const res = await axios.delete(`${BASE_URL}/${userId}`);
  return res.data;
};

export const activateUser = async (userId: string) => {
  const res = await axios.post(`${BASE_URL}/${userId}/activate`);
  return res.data;
};

export const deactivateUser = async (userId: string) => {
  const res = await axios.post(`${BASE_URL}/${userId}/deactivate`);
  return res.data;
};

export const updateUserPassword = async (userId: string, newPassword: string) => {
  const res = await axios.post(`${BASE_URL}/${userId}/password`, { new_password: newPassword });
  return res.data;
};

export const updateUserLastLogin = async (userId: string) => {
  const res = await axios.post(`${BASE_URL}/${userId}/last-login`);
  return res.data;
};

export const updateUserProfile = async (userId: string, data: Record<string, any>) => {
  const res = await axios.put(`${BASE_URL}/${userId}/profile`, data);
  return res.data;
};

export const fetchUserStats = async (shopDomain: string) => {
  const res = await axios.get(`${BASE_URL}/${shopDomain}/stats`);
  return res.data;
};

export const searchUsers = async (query: string) => {
  const res = await axios.get(`${BASE_URL}/search/`, { params: { query } });
  return res.data;
};
