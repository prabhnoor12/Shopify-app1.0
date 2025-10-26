import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getTitleAnalysis } from '../../../api/seo';
import type { SEOAnalysisRequest } from '../../../api/seo';
import './SEOTitleAnalysis.css';

const SEOTitleAnalysis: React.FC = () => {
  const [url, setUrl] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');

  const mutation = useMutation({
    mutationFn: (request: SEOAnalysisRequest) => getTitleAnalysis(request),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.reset();
    mutation.mutate({ url, primary_keyword: primaryKeyword });
  };

  const getTitleFeedback = (title: string, keyword: string) => {
    const feedback: string[] = [];
    if (!title) {
      feedback.push('No title found.');
      return feedback;
    }
    if (title.length < 30 || title.length > 60) {
      feedback.push('Title length should be between 30 and 60 characters.');
    } else {
      feedback.push('Title length is optimal.');
    }
    if (keyword && !title.toLowerCase().includes(keyword.toLowerCase())) {
      feedback.push('Primary keyword not found in title.');
    } else if (keyword) {
      feedback.push('Primary keyword is present in title.');
    }
    return feedback;
  };

  return (
    <div className="seo-title-analysis">
      <h3>Title Analysis</h3>
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
          {mutation.isPending ? 'Loading...' : 'Analyze Title'}
        </button>
      </form>
      {mutation.isError && <div className="seo-title-error">Failed to fetch title analysis.</div>}
      {mutation.data && (
        <div className="title-output">
          <strong>Title:</strong>
          <div>{mutation.data.title}</div>
          <strong>Length:</strong>
          <div>{mutation.data.title.length} characters</div>
          <strong>Feedback:</strong>
          <ul>
            {getTitleFeedback(mutation.data.title, primaryKeyword).map((fb, idx) => (
              <li key={idx}>{fb}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SEOTitleAnalysis;
