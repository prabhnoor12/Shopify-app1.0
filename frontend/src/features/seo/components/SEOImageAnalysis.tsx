import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getImageAnalysis } from '../../../api/seo';
import type { SEOAnalysisRequest } from '../../../api/seo';
import './SEOImageAnalysis.css';

const SEOImageAnalysis: React.FC = () => {
  const [url, setUrl] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');

  const mutation = useMutation({
    mutationFn: (request: SEOAnalysisRequest) => getImageAnalysis(request),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.reset();
    mutation.mutate({ url, primary_keyword: primaryKeyword });
  };

  return (
    <div className="seo-image-analysis">
      <h3>Image Analysis</h3>
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
          {mutation.isPending ? 'Loading...' : 'Analyze Images'}
        </button>
      </form>
      {mutation.isError && <div className="seo-image-error">Failed to fetch image analysis.</div>}
      {mutation.data && (
        <div className="image-output">
          <strong>Image Details:</strong>
          <ul>
            <li>Total Images: {String(mutation.data.images.total_images)}</li>
            <li>Images without Alt Text: {String(mutation.data.images.images_without_alt)}</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default SEOImageAnalysis;
