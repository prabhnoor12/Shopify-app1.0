import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { analyzeProductUrl } from '../../../api/seo';
import type { SEOAnalysisRequest } from '../../../api/seo';
import './SEOUrlAnalyzer.css';

const SEOUrlAnalyzer: React.FC = () => {
  const [url, setUrl] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');

  const mutation = useMutation({
    mutationFn: (request: SEOAnalysisRequest) => analyzeProductUrl(request),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.reset();
    mutation.mutate({ url, primary_keyword: primaryKeyword });
  };

  return (
    <div className="seo-url-analyzer">
      <h2>SEO URL Analyzer</h2>
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
          {mutation.isPending ? 'Loading...' : 'Analyze SEO'}
        </button>
      </form>
      {mutation.isError && <div className="seo-url-error">Failed to fetch SEO analysis.</div>}
      {mutation.data && (
        <div className="url-analysis-output">
          <strong>Title:</strong> <div>{mutation.data.title}</div>
          <strong>Meta Description:</strong> <div>{mutation.data.meta_description}</div>
          <strong>Readability Score:</strong> <div>{mutation.data.readability_score}</div>
          <strong>TF-IDF Keywords:</strong>
          <ul>
            {mutation.data.tfidf_keywords.map((kw: any, idx: number) => (
              <li key={idx}>{Array.isArray(kw) ? kw[0] : String(kw)}</li>
            ))}
          </ul>
          <strong>LSI Keywords:</strong>
          <ul>
            {mutation.data.lsi_keywords.map((kw: any, idx: number) => (
              <li key={idx}>{Array.isArray(kw) ? kw[0] : String(kw)}</li>
            ))}
          </ul>
          <strong>Overall Score:</strong> <div>{mutation.data.overall_score ?? 'N/A'} / 100</div>
        </div>
      )}
    </div>
  );
};

export default SEOUrlAnalyzer;
