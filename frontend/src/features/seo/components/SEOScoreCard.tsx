import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { analyzeProductUrl } from '../../../api/seo';
import type { SEOAnalysisRequest, SEOAnalysisResponse } from '../../../api/seo';
import './SEOScoreCard.css';

const SEOScoreCard: React.FC = () => {
  const [url, setUrl] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');

  const mutation = useMutation({
    mutationFn: (request: SEOAnalysisRequest) => analyzeProductUrl(request),
  });

  // Recommendations are not in the default response, so we infer them from missing/low values
  const getRecommendations = (data: SEOAnalysisResponse) => {
    const recs: string[] = [];
    if (!data.title || data.title.length < 30 || data.title.length > 60) {
      recs.push('Improve title length (30-60 characters recommended).');
    }
    if (!data.meta_description || data.meta_description.length < 50 || data.meta_description.length > 160) {
      recs.push('Improve meta description length (50-160 characters recommended).');
    }
    if (typeof data.readability_score === 'number' && data.readability_score < 60) {
      recs.push('Increase readability score for broader audience.');
    }
    if (Array.isArray(data.lsi_keywords) && data.lsi_keywords.length < 5) {
      recs.push('Add more semantically related keywords.');
    }
    if (Array.isArray(data.tfidf_keywords) && data.tfidf_keywords.length < 10) {
      recs.push('Add more relevant keywords to content.');
    }
    return recs;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.reset();
    mutation.mutate({ url, primary_keyword: primaryKeyword });
  };

  return (
    <div className="seo-score-card">
      <h2>SEO Score Card</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="url"
          placeholder="Product URL"
          value={url}
          onChange={e => setUrl(e.target.value)}
          required
        />
        <input
          type="text"
          placeholder="Primary Keyword"
          value={primaryKeyword}
          onChange={e => setPrimaryKeyword(e.target.value)}
          required
        />
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Loading...' : 'Get SEO Score'}
        </button>
      </form>
      {mutation.isError && <div className="seo-score-error">Failed to fetch SEO score.</div>}
      {mutation.data && (
        <div className="score-output">
          <strong>Overall SEO Score:</strong>
          <div className="score-value">{mutation.data.overall_score ?? 'N/A'} / 100</div>
          <strong>Recommendations:</strong>
          <ul>
            {getRecommendations(mutation.data).map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SEOScoreCard;
