
import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Card, Spinner, Banner, Page } from '@shopify/polaris';
import './PrivacyPolicy.css';

const PrivacyPolicy = () => {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/privacy-policy.md')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load privacy policy.');
        return res.text();
      })
      .then(setContent)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Page title="Privacy Policy">
      <Card>
        <div className="privacy-policy-container">
          {loading && <Spinner accessibilityLabel="Loading privacy policy" size="large" />}
          {error && (
            <Banner>
              Failed to load privacy policy: {error}
            </Banner>
          )}
          {!loading && !error && (
            <div className="privacy-policy-content">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          )}
        </div>
      </Card>
    </Page>
  );
};

export default PrivacyPolicy;
