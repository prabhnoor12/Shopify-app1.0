import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getKeywordAnalysis } from '../../../api/seo';
import type { SEOAnalysisRequest } from '../../../api/seo';
import './SEOKeywordAnalysis.css';

const SEOKeywordAnalysis: React.FC = () => {
  const [url, setUrl] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');

  const mutation = useMutation({
    mutationFn: (request: SEOAnalysisRequest) => getKeywordAnalysis(request),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.reset();
    mutation.mutate({ url, primary_keyword: primaryKeyword });
  };

  return (
    <div className="seo-keyword-analysis">
      <h3>Keyword Analysis</h3>
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
          {mutation.isPending ? 'Loading...' : 'Analyze Keywords'}
        </button>
      </form>
      {mutation.isError && <div className="seo-keyword-error">Failed to fetch keyword analysis.</div>}
      {mutation.data && (
        <div className="keyword-output">
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
        </div>
      )}
    </div>
  );
};

export default SEOKeywordAnalysis;
