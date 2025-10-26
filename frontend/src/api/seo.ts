import axios from 'axios';

export interface SEOAnalysisRequest {
  url: string;
  primary_keyword: string;
}

export interface SEOAnalysisResponse {
  url: string;
  title: string;
  meta_description?: string;
  readability_score?: number;
  lsi_keywords: any[];
  tfidf_keywords: any[];
  overall_score?: number;
}

export async function analyzeProductUrl(request: SEOAnalysisRequest): Promise<SEOAnalysisResponse> {
  const response = await axios.post<SEOAnalysisResponse>(
    '/api/v1/seo/analyze-url',
    request
  );
  return response.data;
}

export async function getTitleAnalysis(request: SEOAnalysisRequest): Promise<{ title: string }> {
  const response = await axios.post<{ title: string }>(
    '/api/v1/seo/title-analysis',
    request
  );
  return response.data;
}

export async function getMetaDescriptionAnalysis(request: SEOAnalysisRequest): Promise<{ meta_description: string }> {
  const response = await axios.post<{ meta_description: string }>(
    '/api/v1/seo/meta-description-analysis',
    request
  );
  return response.data;
}

export async function getReadabilityScore(request: SEOAnalysisRequest): Promise<{ readability_score: number }> {
  const response = await axios.post<{ readability_score: number }>(
    '/api/v1/seo/readability-score',
    request
  );
  return response.data;
}

export async function getKeywordAnalysis(request: SEOAnalysisRequest): Promise<{ lsi_keywords: any[]; tfidf_keywords: any[] }> {
  const response = await axios.post<{ lsi_keywords: any[]; tfidf_keywords: any[] }>(
    '/api/v1/seo/keyword-analysis',
    request
  );
  return response.data;
}

export async function getHeadingAnalysis(request: SEOAnalysisRequest): Promise<{ headings: any }> {
  const response = await axios.post<{ headings: any }>(
    '/api/v1/seo/heading-analysis',
    request
  );
  return response.data;
}

export async function getImageAnalysis(request: SEOAnalysisRequest): Promise<{ images: any }> {
  const response = await axios.post<{ images: any }>(
    '/api/v1/seo/image-analysis',
    request
  );
  return response.data;
}

export async function getLinkAnalysis(request: SEOAnalysisRequest, your_domain: string): Promise<{ links: any }> {
  const response = await axios.post<{ links: any }>(
    '/api/v1/seo/link-analysis',
    request,
    { params: { your_domain } }
  );
  return response.data;
}

export async function getAISuggestions(request: SEOAnalysisRequest): Promise<{ suggestions: string }> {
  const response = await axios.post<{ suggestions: string }>(
    '/api/v1/seo/ai-suggestions',
    request
  );
  return response.data;
}
