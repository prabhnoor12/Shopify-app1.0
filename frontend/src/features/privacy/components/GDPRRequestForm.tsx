import React, { useState } from 'react';
import { Card, Button, Form, FormLayout, TextField, Select, Banner } from '@shopify/polaris';
import axios from 'axios';
import './GDPRRequestForm.css';

interface GDPRRequestFormProps {
  onSuccess?: () => void;
}

export const GDPRRequestForm: React.FC<GDPRRequestFormProps> = ({ onSuccess }) => {
  const [email, setEmail] = useState('');
  const [requestType, setRequestType] = useState('access');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleSubmit = async () => {
    if (!email) {
      setMessage({ type: 'error', text: 'Email is required' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const response = await axios.post('/api/gdpr/data-request', {
        email,
        request_type: requestType,
        reason: reason || undefined,
      });

      setMessage({
        type: 'success',
        text: `Your ${requestType} request has been submitted successfully. Request ID: ${response.data.request_id}`
      });

      // Reset form
      setEmail('');
      setReason('');
      onSuccess?.();
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to submit request. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <div className="gdpr-card">
        <h3 className="gdpr-title">GDPR Data Rights Request</h3>
        <p className="gdpr-description">
          Under GDPR, you have the right to access your personal data or request its deletion.
          Submit a request below and we'll process it within 30 days.
        </p>

        {message && (
          <div className="gdpr-banner">
            <Banner
              tone={message.type === 'error' ? 'critical' : 'success'}
              onDismiss={() => setMessage(null)}
            >
              {message.text}
            </Banner>
          </div>
        )}

        <Form onSubmit={handleSubmit}>
          <FormLayout>
            <TextField
              label="Email Address"
              type="email"
              value={email}
              onChange={setEmail}
              placeholder="your-email@example.com"
              helpText="The email address associated with your account"
              autoComplete="email"
            />

            <Select
              label="Request Type"
              options={[
                { label: 'Access My Data', value: 'access' },
                { label: 'Delete My Data', value: 'delete' },
              ]}
              value={requestType}
              onChange={setRequestType}
            />

            <TextField
              label="Reason (Optional)"
              value={reason}
              onChange={setReason}
              multiline={3}
              placeholder="Please provide any additional context for your request..."
              helpText="Optional: Explain why you're making this request"
              autoComplete="off"
            />

            <Button
              variant="primary"
              submit
              loading={loading}
              disabled={!email}
            >
              Submit Request
            </Button>
          </FormLayout>
        </Form>
      </div>
    </Card>
  );
};
