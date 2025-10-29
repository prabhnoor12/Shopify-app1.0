import axios from 'axios';

const BASE_URL = '/api/product'; // This will be prefixed by BASE_API_URL in client.ts

export const createProduct = async (data: Record<string, any>) => {
  const res = await axios.post(`${BASE_URL}/`, data);
  return res.data;
};

export const fetchProducts = async () => {
  const res = await axios.get(`${BASE_URL}/`);
  return res.data;
};

export const fetchProductById = async (productId: string) => {
  const res = await axios.get(`${BASE_URL}/${productId}`);
  return res.data;
};

export const updateProduct = async (productId: string, data: Record<string, any>) => {
  const res = await axios.put(`${BASE_URL}/${productId}`, data);
  return res.data;
};

export const deleteProduct = async (productId: string) => {
  const res = await axios.delete(`${BASE_URL}/${productId}`);
  return res.data;
};

export const fetchProductView = async () => {
  const res = await axios.get(`${BASE_URL}/view`);
  return res.data;
};
