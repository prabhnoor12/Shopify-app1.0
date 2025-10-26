// src/api/abTestingApi.ts
import { client } from './client';

export const abTestingApi = {
  getTests: () => client.get('/api/ab-tests'),
  getTest: (id: number) => client.get(`/api/ab-tests/${id}`),
  createTest: (data: any) => client.post('/api/ab-tests', data),
  updateTest: (id: number, data: any) => client.put(`/api/ab-tests/${id}`, data),
  deleteTest: (id: number) => client.delete(`/api/ab-tests/${id}`),
  getResults: (id: number) => client.get(`/api/ab-tests/${id}/results`),
  startTest: (id: number) => client.post(`/api/experiments/${id}/start`, {}),
  pauseTest: (id: number) => client.post(`/api/experiments/${id}/pause`, {}),
  endTest: (id: number) => client.post(`/api/experiments/${id}/stop`, {}),
  declareWinner: (id: number, variantId: number) => client.post(`/api/ab-tests/${id}/declare-winner`, { variant_id: variantId }),
  getRecommendations: (testId: number) => client.get(`/api/ab-tests/${testId}/recommendations`),
  getGeneralRecommendations: () => client.get('/api/ai-recommendations'),
};
