import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Form,
  FormLayout,
  Checkbox,
  Banner,
  Layout,
  Page,
  TextField,
  Select,
  Spinner,
  Tabs,
  TextContainer,
  Link
} from '@shopify/polaris';
import axios from 'axios';
import './PrivacyDashboard.css';

interface ConsentPreferences {
  necessary_cookies: boolean;
  analytics_cookies: boolean;
  marketing_cookies: boolean;
  functional_cookies: boolean;
  marketing_emails: boolean;
  product_updates: boolean;
  third_party_sharing: boolean;
  profiling: boolean;
  object_marketing: boolean;
  object_profiling: boolean;
}

export const PrivacyDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [consent, setConsent] = useState<ConsentPreferences | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Data export states
  const [exportFormat, setExportFormat] = useState('json');
  const [exportLoading, setExportLoading] = useState(false);

  // Data rectification states
  const [rectifyField, setRectifyField] = useState('');
  const [rectifyValue, setRectifyValue] = useState('');
  const [rectifyReason, setRectifyReason] = useState('');
  const [rectifyLoading, setRectifyLoading] = useState(false);

  // Objection states
  const [objectType, setObjectType] = useState('');
  const [objectReason, setObjectReason] = useState('');
  const [objectLoading, setObjectLoading] = useState(false);

  // Consent withdrawal states
  const [withdrawType, setWithdrawType] = useState('');
  const [withdrawLoading, setWithdrawLoading] = useState(false);

  useEffect(() => {
    loadConsentPreferences();
  }, []);

  const loadConsentPreferences = async () => {
    try {
      const response = await axios.get('/api/consent/preferences');
      setConsent(response.data.preferences);
    } catch (error) {
      console.error('Failed to load consent preferences:', error);
    }
  };

  const updateConsent = async (preferences: ConsentPreferences) => {
    setLoading(true);
    setMessage(null);

    try {
      await axios.put('/api/consent/preferences', {
        preferences,
        ip_address: 'web-client', // In production, get from request
        user_agent: navigator.userAgent
      });

      setConsent(preferences);
      setMessage({ type: 'success', text: 'Consent preferences updated successfully.' });
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to update consent preferences.'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleConsentChange = (field: keyof ConsentPreferences) => (checked: boolean) => {
    if (!consent) return;

    const newConsent = { ...consent, [field]: checked };
    setConsent(newConsent);
  };

  const handleExportData = async () => {
    setExportLoading(true);
    setMessage(null);

    try {
      const response = await axios.get(`/api/gdpr/data-export/0?format=${exportFormat}`, {
        responseType: 'blob' // For file downloads
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `personal-data.${exportFormat}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setMessage({ type: 'success', text: 'Data export completed successfully.' });
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to export data.'
      });
    } finally {
      setExportLoading(false);
    }
  };

  const handleRectifyData = async () => {
    if (!rectifyField || !rectifyValue) {
      setMessage({ type: 'error', text: 'Field and new value are required.' });
      return;
    }

    setRectifyLoading(true);
    setMessage(null);

    try {
      await axios.put('/api/gdpr/rectify-data', {
        email: 'user@example.com', // In production, get from auth context
        field: rectifyField,
        new_value: rectifyValue,
        reason: rectifyReason
      });

      setMessage({ type: 'success', text: 'Data rectification request submitted successfully.' });
      setRectifyField('');
      setRectifyValue('');
      setRectifyReason('');
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to submit rectification request.'
      });
    } finally {
      setRectifyLoading(false);
    }
  };

  const handleWithdrawConsent = async () => {
    if (!withdrawType) {
      setMessage({ type: 'error', text: 'Please select a consent type to withdraw.' });
      return;
    }

    setWithdrawLoading(true);
    setMessage(null);

    try {
      await axios.post('/api/consent/withdraw', {
        consent_type: withdrawType
      });

      setMessage({ type: 'success', text: `Successfully withdrew consent for ${withdrawType}.` });
      setWithdrawType('');
      loadConsentPreferences(); // Reload preferences
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to withdraw consent.'
      });
    } finally {
      setWithdrawLoading(false);
    }
  };

  const handleObjectToProcessing = async () => {
    if (!objectType) {
      setMessage({ type: 'error', text: 'Please select a processing type to object to.' });
      return;
    }

    setObjectLoading(true);
    setMessage(null);

    try {
      await axios.post('/api/consent/object', {
        objection_type: objectType,
        reason: objectReason || undefined
      });

      setMessage({ type: 'success', text: `Successfully objected to ${objectType} processing.` });
      setObjectType('');
      setObjectReason('');
      loadConsentPreferences(); // Reload preferences
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to record objection.'
      });
    } finally {
      setObjectLoading(false);
    }
  };

  const tabs = [
    { id: 'consent', content: 'Consent Management' },
    { id: 'data-rights', content: 'Data Rights' },
    { id: 'cookie-preferences', content: 'Cookie Preferences' },
    { id: 'privacy-settings', content: 'Privacy Settings' }
  ];

  // Data erasure states
  const [erasureLoading, setErasureLoading] = useState(false);
  const [showEraseConfirm, setShowEraseConfirm] = useState(false);

  const handleEraseData = async () => {
    setErasureLoading(true);
    setMessage(null);
    try {
      await axios.post('/api/gdpr/erase-data', {
        email: 'user@example.com' // In production, get from auth context
      });
      setMessage({ type: 'success', text: 'Your data erasure request has been submitted. Your account and all personal data will be deleted.' });
      setShowEraseConfirm(false);
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to submit data erasure request.'
      });
    } finally {
      setErasureLoading(false);
    }
  };

  if (!consent) {
    return (
      <Page title="Privacy Dashboard">
        <Layout>
          <Layout.Section>
            <Card>
              <div className="privacy-dashboard-loading">
                <Spinner size="large" />
                <p>Loading privacy preferences...</p>
              </div>
            </Card>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <Page title="Privacy Dashboard">
      <Layout>
        <Layout.Section>
          {message && (
            <Banner tone={message.type === 'error' ? 'critical' : 'success'} onDismiss={() => setMessage(null)}>
              {message.text}
            </Banner>
          )}

          <Card>
            <Tabs tabs={tabs} selected={activeTab} onSelect={setActiveTab}>
              {/* Consent Management Tab */}
              {activeTab === 0 && (
                <div>
                  <h2>Manage Your Consent Preferences</h2>
                  <TextContainer>
                    <p>Control how we use your data. You can change these preferences at any time.</p>
                  </TextContainer>

                  <Form onSubmit={() => updateConsent(consent)}>
                    <FormLayout>
                      <h3>Cookies</h3>
                      <Checkbox
                        label="Necessary Cookies (Required for website functionality)"
                        checked={consent.necessary_cookies}
                        disabled // Always required
                      />
                      <Checkbox
                        label="Analytics Cookies (Help us improve our service)"
                        checked={consent.analytics_cookies}
                        onChange={handleConsentChange('analytics_cookies')}
                      />
                      <Checkbox
                        label="Marketing Cookies (Used for advertising)"
                        checked={consent.marketing_cookies}
                        onChange={handleConsentChange('marketing_cookies')}
                      />
                      <Checkbox
                        label="Functional Cookies (Enhance your experience)"
                        checked={consent.functional_cookies}
                        onChange={handleConsentChange('functional_cookies')}
                      />

                      <h3>Communications</h3>
                      <Checkbox
                        label="Marketing Emails"
                        checked={consent.marketing_emails}
                        onChange={handleConsentChange('marketing_emails')}
                      />
                      <Checkbox
                        label="Product Updates"
                        checked={consent.product_updates}
                        onChange={handleConsentChange('product_updates')}
                      />

                      <h3>Data Processing</h3>
                      <Checkbox
                        label="Third-party Data Sharing"
                        checked={consent.third_party_sharing}
                        onChange={handleConsentChange('third_party_sharing')}
                      />
                      <Checkbox
                        label="Profiling and Automated Decision Making"
                        checked={consent.profiling}
                        onChange={handleConsentChange('profiling')}
                      />

                      <Button variant="primary" loading={loading}>
                        Save Preferences
                      </Button>
                    </FormLayout>
                  </Form>
                </div>
              )}

              {/* Data Rights Tab */}
              {activeTab === 1 && (
                <div>
                  <h2>Exercise Your Data Rights</h2>
                  <TextContainer>
                    <p>Under GDPR and CCPA, you have several rights regarding your personal data.</p>
                  </TextContainer>

                  <Layout>
                    <Layout.Section>
                      <Card>
                        <TextContainer>
                          <h3>Data Export</h3>
                        </TextContainer>
                        <Select
                          label="Export Format"
                          options={[
                            { label: 'JSON', value: 'json' },
                            { label: 'CSV', value: 'csv' },
                            { label: 'XML', value: 'xml' }
                          ]}
                          value={exportFormat}
                          onChange={setExportFormat}
                        />
                        <br />
                        <Button
                          variant="primary"
                          loading={exportLoading}
                          onClick={handleExportData}
                        >
                          Export My Data
                        </Button>
                      </Card>
                    </Layout.Section>

                    <Layout.Section>
                      <Card>
                        <TextContainer>
                          <h3>Data Rectification</h3>
                        </TextContainer>
                        <Form onSubmit={handleRectifyData}>
                          <FormLayout>
                            <Select
                              label="Field to Update"
                              options={[
                                { label: 'Email Address', value: 'email' },
                                { label: 'Shop Domain', value: 'shop_domain' },
                                { label: 'Plan', value: 'plan' }
                              ]}
                              value={rectifyField}
                              onChange={setRectifyField}
                            />
                            <TextField
                              label="New Value"
                              value={rectifyValue}
                              onChange={setRectifyValue}
                              autoComplete="off"
                            />
                            <TextField
                              label="Reason (Optional)"
                              value={rectifyReason}
                              onChange={setRectifyReason}
                              autoComplete="off"
                            />
                            <Button
                              variant="primary"
                              loading={rectifyLoading}
                            >
                              Request Rectification
                            </Button>
                          </FormLayout>
                        </Form>
                      </Card>
                    </Layout.Section>
                  </Layout>
                  {/* Data Erasure (Right to be Forgotten) */}
                  <Card>
                    <TextContainer>
                      <h3>Delete My Account & Data</h3>
                      <p>You can request deletion of your account and all personal data. This action is irreversible.</p>
                    </TextContainer>
                    <Button
                      variant="primary"
                      tone="critical"
                      loading={erasureLoading}
                      onClick={() => setShowEraseConfirm(true)}
                    >
                      Delete My Account & Data
                    </Button>
                    {showEraseConfirm && (
                      <div className="erase-confirm-banner">
                        <Banner tone="critical">
                          <p>Are you sure? This will permanently delete your account and all personal data. This cannot be undone.</p>
                          <Button
                            variant="primary"
                            tone="critical"
                            loading={erasureLoading}
                            onClick={handleEraseData}
                          >
                            Yes, Delete Everything
                          </Button>
                          <div className="erase-cancel-btn">
                            <Button
                              onClick={() => setShowEraseConfirm(false)}
                            >
                              Cancel
                            </Button>
                          </div>
                        </Banner>
                      </div>
                    )}
                  </Card>
                </div>
              )}
              {activeTab === 2 && (
                <div>
                  <h2>Cookie Preferences</h2>
                  <TextContainer>
                    <p>Manage your cookie preferences below. You can enable or disable each type of cookie except those necessary for the website to function.</p>
                  </TextContainer>
                  <Form onSubmit={() => updateConsent(consent)}>
                    <FormLayout>
                      <Checkbox
                        label="Necessary Cookies (Required for website functionality)"
                        checked={consent.necessary_cookies}
                        disabled
                      />
                      <Checkbox
                        label="Analytics Cookies"
                        checked={consent.analytics_cookies}
                        onChange={handleConsentChange('analytics_cookies')}
                      />
                      <Checkbox
                        label="Marketing Cookies"
                        checked={consent.marketing_cookies}
                        onChange={handleConsentChange('marketing_cookies')}
                      />
                      <Checkbox
                        label="Functional Cookies"
                        checked={consent.functional_cookies}
                        onChange={handleConsentChange('functional_cookies')}
                      />
                      <Button variant="primary" loading={loading}>
                        Save Cookie Preferences
                      </Button>
                    </FormLayout>
                  </Form>
                </div>
              )}


              {/* Privacy Settings Tab */}
              {activeTab === 3 && (
                <div>
                  <h2>Privacy Settings</h2>

                  <Card>
                    <TextContainer>
                      <h3>Withdraw Consent</h3>
                    </TextContainer>
                    <TextContainer>
                      <p>Select a specific consent type to withdraw:</p>
                    </TextContainer>
                    <FormLayout>
                      <Select
                        label="Consent Type"
                        options={[
                          { label: 'Analytics Cookies', value: 'analytics_cookies' },
                          { label: 'Marketing Cookies', value: 'marketing_cookies' },
                          { label: 'Functional Cookies', value: 'functional_cookies' },
                          { label: 'Marketing Emails', value: 'marketing_emails' },
                          { label: 'Product Updates', value: 'product_updates' },
                          { label: 'Third-party Sharing', value: 'third_party_sharing' },
                          { label: 'Profiling', value: 'profiling' }
                        ]}
                        value={withdrawType}
                        onChange={setWithdrawType}
                      />
                      <Button
                        variant="primary"
                        loading={withdrawLoading}
                        onClick={handleWithdrawConsent}
                      >
                        Withdraw Consent
                      </Button>
                    </FormLayout>
                  </Card>

                  <Card>
                    <TextContainer>
                      <h3>Right to Object</h3>
                    </TextContainer>
                    <TextContainer>
                      <p>Exercise your right to object to data processing based on legitimate interests:</p>
                    </TextContainer>
                    <FormLayout>
                      <Select
                        label="Processing Type"
                        options={[
                          { label: 'Marketing Communications', value: 'marketing' },
                          { label: 'Profiling and Analytics', value: 'profiling' }
                        ]}
                        value={objectType}
                        onChange={setObjectType}
                      />
                      <TextField
                        label="Reason (Optional)"
                        value={objectReason}
                        onChange={setObjectReason}
                        autoComplete="off"
                      />
                      <Button
                        variant="primary"
                        loading={objectLoading}
                        onClick={handleObjectToProcessing}
                      >
                        Object to Processing
                      </Button>
                    </FormLayout>
                  </Card>

                  <Card>
                    <TextContainer>
                      <h3>Additional Resources</h3>
                    </TextContainer>
                    <TextContainer>
                      <p>
                        <Link url="/privacy-policy">View our Privacy Policy</Link>
                      </p>
                      <p>
                        <Link url="/data-retention-policy">View our Data Retention Policy</Link>
                      </p>
                      <p>
                        For additional privacy concerns, contact our Data Protection Officer at{' '}
                        <Link url="mailto:dpo@yourcompany.com">dpo@yourcompany.com</Link>
                      </p>
                    </TextContainer>
                  </Card>
                </div>
              )}
            </Tabs>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
};
