import axios from 'axios';

const BASE_URL = '/api/dashboard';

export const fetchUserDashboard = async (userId: string) => {
  const res = await axios.get(`${BASE_URL}/user/${userId}`);
  return res.data;
};

export const fetchUserSummary = async (userId: string) => {
  const res = await axios.get(`${BASE_URL}/user/${userId}/summary`);
  return res.data;
};

export const fetchUserActivity = async (userId: string) => {
  const res = await axios.get(`${BASE_URL}/user/${userId}/activity`);
  return res.data;
};

export const fetchRecentDescriptions = async (userId: string) => {
  const res = await axios.get(`${BASE_URL}/user/${userId}/recent-descriptions`);
  return res.data;
};

export const fetchTeamActivity = async (teamId: string) => {
  const res = await axios.get(`${BASE_URL}/team/${teamId}/activity`);
  return res.data;
};

export const fetchMonthlyCounts = async () => {
  const res = await axios.get(`${BASE_URL}/descriptions/monthly-counts`);
  return res.data;
};

export const fetchTopProducts = async () => {
  const res = await axios.get(`${BASE_URL}/top-products`);
  return res.data;
};

export const fetchRecentOrders = async () => {
  const res = await axios.get(`${BASE_URL}/recent-orders`);
  return res.data;
};

export const fetchSalesTrend = async () => {
  const res = await axios.get(`${BASE_URL}/sales-trend`);
  return res.data;
};
