import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getReadabilityScore } from '../../../api/seo';
import type { SEOAnalysisRequest } from '../../../api/seo';
import './SEOReadability.css';

const SEOReadability: React.FC = () => {
  const [url, setUrl] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');

  const mutation = useMutation({
    mutationFn: (request: SEOAnalysisRequest) => getReadabilityScore(request),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.reset();
    mutation.mutate({ url, primary_keyword: primaryKeyword });
  };

  return (
    <div className="seo-readability">
      <h3>Readability Score</h3>
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
          {mutation.isPending ? 'Loading...' : 'Analyze Readability'}
        </button>
      </form>
      {mutation.isError && <div className="seo-readability-error">Failed to fetch readability score.</div>}
      {mutation.data && (
        <div className="readability-output">
          <strong>Flesch Reading Ease Score:</strong>
          <div>{mutation.data.readability_score}</div>
          <ReadabilityInterpretation score={mutation.data.readability_score} />
        </div>
      )}
    </div>
  );
};

// Helper component for interpretation
const ReadabilityInterpretation: React.FC<{ score?: number }> = ({ score }) => {
  if (score === undefined || score === null) return null;
  let level = '';
  let className = '';
  if (score >= 90) {
    level = 'Very Easy (5th grade)';
    className = 'readability-very-easy';
  } else if (score >= 80) {
    level = 'Easy (6th grade)';
    className = 'readability-easy';
  } else if (score >= 70) {
    level = 'Fairly Easy (7th grade)';
    className = 'readability-fairly-easy';
  } else if (score >= 60) {
    level = 'Standard (8th-9th grade)';
    className = 'readability-standard';
  } else if (score >= 50) {
    level = 'Fairly Difficult (10th-12th grade)';
    className = 'readability-fairly-difficult';
  } else if (score >= 30) {
    level = 'Difficult (College)';
    className = 'readability-difficult';
  } else {
    level = 'Very Confusing (College Graduate)';
    className = 'readability-very-confusing';
  }
  return (
    <div className={className + ' readability-interpretation'}>
      <strong>Interpretation:</strong> {level}
    </div>
  );
};

export default SEOReadability;
