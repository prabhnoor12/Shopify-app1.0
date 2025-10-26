// src/api/shopApi.ts
import { client } from './client';

export interface BrandVoice {
  tone_of_voice: string;
  vocabulary_preferences: {
    preferred: string[];
    avoid: string[];
  };
  industry_jargon: string[];
  banned_words: string[];
}

// Mock data for development
const isDev = import.meta.env.MODE === 'development';

const mockProducts = [
  { id: '1', title: 'Mock T-Shirt' },
  { id: '2', title: 'Mock Hoodie' },
  { id: '3', title: 'Mock Mug' },
];

const mockBrandVoice = {
  tone_of_voice: 'Friendly',
  vocabulary_preferences: {
    preferred: ['innovative', 'sustainable'],
    avoid: ['cheap', 'boring'],
  },
  industry_jargon: ['SKU', 'dropshipping'],
  banned_words: ['hate', 'fake'],
};

const mockBulkReplaceResult = {
  updated_products: ['1', '2'],
  errors: [{ product_id: '3', error: 'No match found' }],
  total_matches: 2,
};

export const shopApi = {
  getProducts: () => isDev ? Promise.resolve(mockProducts) : client.get('/api/products'),
  bulkFindReplace: (data: any) => isDev ? Promise.resolve(mockBulkReplaceResult) : client.post('/api/bulk-find-replace', data),
  generateDescription: (data: any) => isDev ? Promise.resolve({
    descriptions: ['Mock description 1', 'Mock description 2'],
    keywords: ['mock', 'test'],
    meta_title: 'Mock Meta Title',
    meta_description: 'Mock meta description',
    seo_analysis: {},
    seo_suggestions: {},
  }) : client.post('/api/generate-description', data),
  generateFromImage: (data: any) => isDev ? Promise.resolve({
    descriptions: ['Image-based mock description'],
    keywords: ['image', 'mock'],
    meta_title: 'Image Mock Title',
    meta_description: 'Image mock meta description',
    seo_analysis: {},
    seo_suggestions: {},
  }) : client.post('/api/generate-description-from-image', data),
  generateFromUrl: (data: any) => isDev ? Promise.resolve({
    descriptions: ['URL-based mock description'],
    keywords: ['url', 'mock'],
    meta_title: 'URL Mock Title',
    meta_description: 'URL mock meta description',
    seo_analysis: {},
    seo_suggestions: {},
  }) : client.post('/api/generate-description-from-url', data),
  saveDescription: (data: any) => isDev ? Promise.resolve({ success: true }) : client.post('/api/save-description', data),
  bulkGenerateDescriptions: (data: any) => isDev ? Promise.resolve([{ id: '1', description: 'Bulk mock desc' }]) : client.post('/api/bulk-generate-descriptions', data),
  bulkSaveDescriptions: (data: any) => isDev ? Promise.resolve({ success: true }) : client.post('/api/bulk-save-descriptions', data),
  regenerateVariant: (data: any) => isDev ? Promise.resolve({ description: 'Regenerated mock variant' }) : client.post('/api/regenerate-variant', data),
  transformFeatureToBenefit: (data: any) => isDev ? Promise.resolve({ benefit: 'Mock benefit' }) : client.post('/api/transform-feature-to-benefit', data),
  getBrandVoice: (): Promise<BrandVoice> => isDev ? Promise.resolve(mockBrandVoice) : client.get('/api/brand-voice'),
  saveBrandVoice: (data: BrandVoice) => isDev ? Promise.resolve({ success: true }) : client.post('/api/brand-voice', data),
};
