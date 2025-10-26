import axios from 'axios';

const BASE_URL = '/api/analytics';

export const fetchRevenueAttribution = async (productId: string) => {
  const res = await axios.get(`${BASE_URL}/revenue-attribution/${productId}`);
  return res.data;
};

export const fetchDescriptionPerformance = async (productId: string) => {
  const res = await axios.get(`${BASE_URL}/description-performance/${productId}`);
  return res.data;
};

export const analyzeSEO = async (data: Record<string, any>) => {
  const res = await axios.post(`${BASE_URL}/analyze-seo`, data);
  return res.data;
};

export const fetchProductTimelinePerformance = async (productId: string) => {
  const res = await axios.get(`${BASE_URL}/product-timeline-performance/${productId}`);
  return res.data;
};

export const fetchTeamPerformance = async (teamId: string) => {
  const res = await axios.get(`${BASE_URL}/team-performance/${teamId}`);
  return res.data;
};

export const fetchActionableAlerts = async () => {
  const res = await axios.get(`${BASE_URL}/actionable-alerts`);
  return res.data;
};

export const generateSEOSuggestions = async (data: Record<string, any>) => {
  const res = await axios.post(`${BASE_URL}/generate-seo-suggestions`, data);
  return res.data;
};

export const fetchCategoryPerformance = async () => {
  const res = await axios.get(`${BASE_URL}/category-performance`);
  return res.data;
}
