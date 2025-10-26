import { useState, useEffect } from 'react';
import {
  Card,
  Text,
  Spinner,
  Banner,
  ProgressBar,
  LegacyStack,
  TextContainer,
  Box,
} from '@shopify/polaris';
import { userApi } from '../../../api/userApi';
import type { UserStatus } from '../../../api/userApi';
import './UserAccountStatus.css';

const UserAccountStatus = () => {
  const [status, setStatus] = useState<UserStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let didTimeout = false;
    const timeout = setTimeout(() => {
      didTimeout = true;
      setLoading(false);
    }, 5000);

    const fetchStatus = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await userApi.getStatus();
        if (!didTimeout) setStatus(response);
      } catch (err: any) {
        if (!didTimeout) setError(err.message);
      } finally {
        if (!didTimeout) setLoading(false);
      }
    };

    fetchStatus();
    return () => clearTimeout(timeout);
  }, []);

  if (loading) {
    return (
      <Card>
        <Text variant="headingMd" as="h2">
          User Account Status
        </Text>
        <Box padding="400">
          <Spinner accessibilityLabel="Loading user status" size="large" />
        </Box>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <Text variant="headingMd" as="h2">
          User Account Status
        </Text>
        <Box padding="400">
          <Banner tone="critical">{error}</Banner>
        </Box>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card>
        <Text variant="headingMd" as="h2">
          User Account Status
        </Text>
        <Box padding="400">
          <Text as="p">Could not load user account status.</Text>
        </Box>
      </Card>
    );
  }

  const generationPercentage =
    (status.generations_used / status.monthly_generation_limit) * 100;
  const trialDaysLeft = status.trial_ends_at
    ? Math.ceil(
        (new Date(status.trial_ends_at).getTime() - new Date().getTime()) /
          (1000 * 60 * 60 * 24),
      )
    : 0;

  return (
    <div className="user-account-status">
      <Card>
        <Text variant="headingMd" as="h2">
          Account Status
        </Text>
        <Box padding="400">
          <LegacyStack vertical>
            <LegacyStack distribution="equalSpacing">
              <Text as="p" fontWeight="bold">
                Current Plan:
              </Text>
              <Text as="p">{status.plan}</Text>
            </LegacyStack>
            {status.trial_ends_at && trialDaysLeft > 0 && (
              <LegacyStack distribution="equalSpacing">
                <Text as="p" fontWeight="bold">
                  Trial Ends:
                </Text>
                <Text as="p">{trialDaysLeft} days left</Text>
              </LegacyStack>
            )}
            <TextContainer>
              <Text as="p" fontWeight="bold">
                Monthly Generations:
              </Text>
              <ProgressBar progress={generationPercentage} />
              <Text as="p" alignment="end">
                {status.generations_used} / {status.monthly_generation_limit}
              </Text>
            </TextContainer>
          </LegacyStack>
        </Box>
      </Card>
    </div>
  );
};

export default UserAccountStatus;
