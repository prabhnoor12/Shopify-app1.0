import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getLinkAnalysis } from '../../../api/seo';
import type { SEOAnalysisRequest } from '../../../api/seo';
import './SEOLinkAnalysis.css';

const SEOLinkAnalysis: React.FC = () => {
  const [url, setUrl] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');
  const [yourDomain, setYourDomain] = useState('');

  const mutation = useMutation({
    mutationFn: (variables: { request: SEOAnalysisRequest; yourDomain: string }) =>
      getLinkAnalysis(variables.request, variables.yourDomain),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.reset();
    mutation.mutate({
      request: { url, primary_keyword: primaryKeyword },
      yourDomain,
    });
  };

  return (
    <div className="seo-link-analysis">
      <h3>Link Analysis</h3>
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
        <input
          type="text"
          placeholder="Your Domain (for internal links)"
          value={yourDomain}
          onChange={e => setYourDomain(e.target.value)}
          required
        />
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Loading...' : 'Analyze Links'}
        </button>
      </form>
      {mutation.isError && <div className="seo-link-error">Failed to fetch link analysis.</div>}
      {mutation.data && (
        <div className="link-output">
          <strong>Link Details:</strong>
          <ul>
            <li>Internal Links: {String(mutation.data.links.internal_links)}</li>
            <li>External Links: {String(mutation.data.links.external_links)}</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default SEOLinkAnalysis;
