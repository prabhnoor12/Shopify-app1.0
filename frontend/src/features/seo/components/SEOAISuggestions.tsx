import React, { useState } from 'react';
import { getAISuggestions } from '../../../api/seo';
import type { SEOAnalysisRequest } from '../../../api/seo';
import './SEOAISuggestions.css';

const SEOAISuggestions: React.FC = () => { 
  const [url, setUrl] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');
  const [suggestions, setSuggestions] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuggestions('');
    try {
      const request: SEOAnalysisRequest = {
        url,
        primary_keyword: primaryKeyword,
      };
      const response = await getAISuggestions(request);
      setSuggestions(response.suggestions);
    } catch (err: any) {
      setError('Failed to fetch AI suggestions.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="seo-ai-suggestions">
      <h3>AI SEO Suggestions</h3>
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
        <button type="submit" disabled={loading}>
          {loading ? 'Loading...' : 'Get Suggestions'}
        </button>
      </form>
      {error && <div className="seo-ai-error">{error}</div>}
      {suggestions && (
        <div className="suggestions-output">
          <strong>Suggestions:</strong>
          <pre>{suggestions}</pre>
        </div>
      )}
    </div>
  );
};

export default SEOAISuggestions;
