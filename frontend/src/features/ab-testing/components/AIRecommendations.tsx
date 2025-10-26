import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Text,
  Button,
  Spinner,
  Banner,
  BlockStack,
  InlineStack,
  Tooltip,
  Icon,
  EmptyState,
} from '@shopify/polaris';
import { InfoIcon } from '@shopify/polaris-icons';
import { abTestingApi } from '../../../api/abTestingApi';
import './AIRecommendations.css';
import { useNavigate } from 'react-router-dom';

// Define the structure for a single AI recommendation from the API
interface ApiRecommendation {
  id: string;
  title: string;
  description: string;
  confidence: number;
  action_type: 'run_test' | 'create_variant' | 'analyze_pricing';
  action_payload: {
    productId?: string;
    page?: string;
  };
}

// Enhanced Recommendation structure for the component
interface Recommendation extends ApiRecommendation {
  action: {
    label: string;
    onClick: () => void;
  };
}

interface AIRecommendationsProps {
  productId?: string;
  forceStopLoading?: boolean;
}

const AIRecommendations: React.FC<AIRecommendationsProps> = ({ productId, forceStopLoading }) => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleAction = (rec: ApiRecommendation) => {
    switch (rec.action_type) {
      case 'run_test':
        // Example: Navigate to the A/B test creation wizard with pre-filled data
        navigate(`/ab-testing/new?productId=${rec.action_payload.productId}&recommendation=${rec.id}`);
        break;
      case 'create_variant':
        // Example: Navigate to a product variant creation page
        navigate(`/products/${rec.action_payload.productId}/variants/new`);
        break;
      case 'analyze_pricing':
        // Example: Navigate to a pricing analysis page
        navigate(`/analytics/pricing?productId=${rec.action_payload.productId}`);
        break;
      default:
        console.log('Unknown action type:', rec.action_type);
    }
  };

  const getActionLabel = (actionType: ApiRecommendation['action_type']): string => {
    switch (actionType) {
      case 'run_test':
        return 'Run A/B Test';
      case 'create_variant':
        return 'Create Variant';
      case 'analyze_pricing':
        return 'Analyze Pricing';
      default:
        return 'View Details';
    }
  };

  const loadRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Use the actual API endpoint
      const apiRecs: ApiRecommendation[] = productId
        ? await abTestingApi.getRecommendations(parseInt(productId, 10))
        : await abTestingApi.getGeneralRecommendations();

      // Map API data to component's recommendation structure with actions
      const processedRecs = apiRecs.map((rec) => ({
        ...rec,
        action: {
          label: getActionLabel(rec.action_type),
          onClick: () => handleAction(rec),
        },
      }));

      setRecommendations(processedRecs);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred while fetching recommendations.');
      }
    } finally {
      setLoading(false);
    }
  }, [productId, navigate]);

  useEffect(() => {
    loadRecommendations();
  }, [loadRecommendations]);

  const renderConfidenceTooltip = (confidence: number) => (
    <Tooltip content={`Confidence Score: ${Math.round(confidence * 100)}%`}>
      <Icon source={InfoIcon} tone="base" />
    </Tooltip>
  );


  if (loading && !forceStopLoading) {
    return (
      <Card>
        <BlockStack gap="400">
          <Text as="h2" variant="headingMd">
            AI Recommendations
          </Text>
          <Spinner accessibilityLabel="Loading recommendations" size="large" />
          <div className="ai-recommendations-help-text">
            <Text as="p" variant="bodyMd" tone="subdued">
              Loading personalized recommendations. This may take a moment for large catalogs.
            </Text>
          </div>
        </BlockStack>
      </Card>
    );
  }

  if (error) {
    return (
      <Banner title="Error loading recommendations" tone="critical">
        <Text as="p" variant="bodyMd" tone="subdued">{error}</Text>
      </Banner>
    );
  }

  return (
    <div className="ai-recommendations-root">
      <div className="ai-recommendations">
        <Card>
          <BlockStack gap="400">
            <Text as="h2" variant="headingMd">
              AI-Powered Recommendations
            </Text>
            <div className="ai-recommendations-section">
              <Text as="p" variant="bodyMd" tone="subdued">
                Get actionable suggestions powered by AI to optimize your products, pricing, and experiments. Click an action to get started.
              </Text>
            </div>
            {recommendations.length > 0 ? (
              <ul className="recommendation-list">
                {recommendations.map((rec) => (
                  <li key={rec.id} className="recommendation-item">
                    <BlockStack gap="200">
                      <InlineStack align="space-between">
                        <Text as="h3" variant="headingSm">
                          {rec.title}
                        </Text>
                        {renderConfidenceTooltip(rec.confidence)}
                      </InlineStack>
                      <Text as="p" tone="subdued">
                        {rec.description}
                      </Text>
                      <div className="recommendation-action">
                        <Button onClick={rec.action.onClick} size="slim">
                          {rec.action.label}
                        </Button>
                      </div>
                    </BlockStack>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                heading="No recommendations available"
                image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
              >
                <Text as="p" variant="bodyMd" tone="subdued">
                  Check back later for AI-powered suggestions to improve your store.
                </Text>
              </EmptyState>
            )}
            <div className="recommendations-footer">
              <Button onClick={loadRecommendations} variant="plain" loading={loading}>
                Refresh Recommendations
              </Button>
            </div>
          </BlockStack>
        </Card>
      </div>
    </div>
  );
};

export default AIRecommendations;
