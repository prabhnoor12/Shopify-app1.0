import React, { useState } from 'react';
import { getHeadingAnalysis } from '../../../api/seo';
import type { SEOAnalysisRequest } from '../../../api/seo';
import './SEOHeadingAnalysis.css';

const SEOHeadingAnalysis: React.FC = () => {
  const [url, setUrl] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');
  const [headings, setHeadings] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setHeadings(null);
    try {
      const request: SEOAnalysisRequest = {
        url,
        primary_keyword: primaryKeyword,
      };
      const response = await getHeadingAnalysis(request);
      setHeadings(response.headings);
    } catch (err: any) {
      setError('Failed to fetch heading analysis.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="seo-heading-analysis">
      <h3>Heading Analysis</h3>
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
          {loading ? 'Loading...' : 'Analyze Headings'}
        </button>
      </form>
      {error && <div className="seo-heading-error">{error}</div>}
      {headings && (
        <div className="heading-output">
          <strong>Heading Counts:</strong>
          <ul>
            {Object.entries(headings).map(([tag, count]) => (
              <li key={tag}>{tag.toString().toUpperCase()}: {String(count)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SEOHeadingAnalysis;
