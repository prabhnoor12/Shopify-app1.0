import './SEOAnalysis.css';
import './AnalyticsCard.css';
import React, { memo } from 'react';

export interface SEOAnalysisData {
  primary_keyword: string;
  title: string;
  description: string;
  meta_title?: string;
  meta_description?: string;
  score: number;
  issues: string[];
  suggestions: string[];
}

interface SEOAnalysisProps {
  data?: SEOAnalysisData | null;
  loading?: boolean;
  error?: string | null;
}

const SEOAnalysis: React.FC<SEOAnalysisProps> = memo(({ data, loading = false, error = null }) => {
  if (loading) {
    return (
      <div className="seo-analysis analytics-card" role="status" aria-busy="true">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#8884d8" strokeWidth="2" opacity="0.3"/><path d="M12 2a10 10 0 0 1 10 10" stroke="#8884d8" strokeWidth="2"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/></path></svg>
          Loading SEO analysis...
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="seo-analysis analytics-card" role="alert">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#ff4d4f" strokeWidth="2" opacity="0.3"/><path d="M12 8v4m0 4h.01" stroke="#ff4d4f" strokeWidth="2" strokeLinecap="round"/></svg>
          {error}
        </div>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="seo-analysis analytics-card" role="status">
        <div className="analytics-card-empty">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#888" strokeWidth="2" opacity="0.2"/><path d="M8 12h8M12 8v8" stroke="#888" strokeWidth="2" strokeLinecap="round"/></svg>
          No SEO analysis data available.
        </div>
      </div>
    );
  }
  return (
    <div className="seo-analysis analytics-card">
      <h2 className="analytics-card-title">SEO Analysis</h2>
      <div className="analytics-card-section">
        <p><strong>Primary Keyword:</strong> {data.primary_keyword}</p>
        <p><strong>Title:</strong> {data.title}</p>
        <p><strong>Description:</strong> {data.description}</p>
        {data.meta_title && <p><strong>Meta Title:</strong> {data.meta_title}</p>}
        {data.meta_description && <p><strong>Meta Description:</strong> {data.meta_description}</p>}
        <p><strong>SEO Score:</strong> {data.score}/100</p>
      </div>
      <div className="analytics-card-section">
        <h3>Issues</h3>
        {data.issues.length === 0 ? <p>No issues found.</p> : (
          <ul aria-label="SEO issues list">
            {data.issues.map((issue, idx) => <li key={idx}>{issue}</li>)}
          </ul>
        )}
      </div>
      <div className="analytics-card-section">
        <h3>Suggestions</h3>
        {data.suggestions.length === 0 ? <p>No suggestions.</p> : (
          <ul aria-label="SEO suggestions list">
            {data.suggestions.map((s, idx) => <li key={idx}>{s}</li>)}
          </ul>
        )}
      </div>
    </div>
  );
});

export default SEOAnalysis;
