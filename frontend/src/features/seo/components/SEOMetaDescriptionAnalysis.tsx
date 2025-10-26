import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getMetaDescriptionAnalysis } from '../../../api/seo';
import type { SEOAnalysisRequest } from '../../../api/seo';
import './SEOMetaDescriptionAnalysis.css';

const SEOMetaDescriptionAnalysis: React.FC = () => {
  const [url, setUrl] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');

  const mutation = useMutation({
    mutationFn: (request: SEOAnalysisRequest) => getMetaDescriptionAnalysis(request),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.reset();
    mutation.mutate({ url, primary_keyword: primaryKeyword });
  };

  return (
    <div className="seo-meta-description-analysis">
      <h3>Meta Description Analysis</h3>
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
          {mutation.isPending ? 'Loading...' : 'Analyze Meta Description'}
        </button>
      </form>
      {mutation.isError && <div className="seo-meta-description-error">Failed to fetch meta description analysis.</div>}
      {mutation.data && (
        <div className="meta-description-output">
          <strong>Meta Description:</strong>
          <div>{mutation.data.meta_description}</div>
        </div>
      )}
    </div>
  );
};

export default SEOMetaDescriptionAnalysis;
