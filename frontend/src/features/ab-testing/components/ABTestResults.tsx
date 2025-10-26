import React, { useState, useEffect, useCallback } from 'react';
// Production-ready: Add PropTypes for runtime validation (if not using TypeScript everywhere)
// import PropTypes from 'prop-types';
import {
  Card,
  Text,
  Spinner,
  Banner,
  Button,
  DataTable,
  LegacyStack,
  DescriptionList,
  Modal,
  Tooltip,
  EmptyState,
} from '@shopify/polaris';
import { abTestingApi } from '../../../api/abTestingApi';

import './ABTestResults.css';
import BarChart from './BarChart';


interface ABTestResultsProps {
  testId: number | null;
  onBack: () => void;
  forceStopLoading?: boolean;
}

interface VariantResult {
  id: number;
  description: string;
  impressions: number;
  conversions: number;
  conversion_rate: number;
  confidence_interval: [number, number];
  total_revenue: number;
  average_order_value: number;
  revenue_per_visitor: number;
  is_winner: boolean;
  segments?: any; // Simplified for this example
}

interface TestResults {
  test_name: string;
  status: string;
  variants: VariantResult[];
  bayesian_probabilities: Record<string, number>;
  p_value: number;
  effect_size: number;
  is_significant: boolean;
  segment_winners?: any;
}

const ABTestResults: React.FC<ABTestResultsProps> = ({ testId, /* onBack, */ forceStopLoading }) => {
  // Handle declaring a winner
  const handleDeclareWinner = async (variantId: number | null) => {
    if (!variantId) return;
    setDeclaringWinner(variantId);
    try {
      // Call API to declare winner (replace with actual API call)
      await abTestingApi.declareWinner(testId!, variantId);
      // Refetch results to update UI
      fetchResults();
      setShowDeclareWinnerModal(null);
    } catch (err: any) {
      setError(err?.message || 'Failed to declare winner.');
    } finally {
      setDeclaringWinner(null);
    }
  };
  // Defensive: Ensure testId is a valid number
  const validTestId = typeof testId === 'number' && !isNaN(testId) && testId > 0;
  const [results, setResults] = useState<TestResults | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [declaringWinner, setDeclaringWinner] = useState<number | null>(null);
  const [showDeclareWinnerModal, setShowDeclareWinnerModal] = useState<number | null>(null);

  // Fetch results with error and abort handling
  const fetchResults = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResults(null);
    if (!validTestId) {
      setError('Invalid test ID.');
      setLoading(false);
      return;
    }
    try {
      const response = await abTestingApi.getResults(testId!);
      setResults(response);
    } catch (err: any) {
      setError(err?.message || 'Failed to load test results. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [testId, validTestId]);

  useEffect(() => {
    fetchResults();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [testId]);

  // Conditional rendering for loading, error, invalid testId, and empty results
  if (!validTestId) {
    return (
      <EmptyState
        heading="Select a test to view results"
        image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
      >
        <p>Select a test from the dashboard to view its results.</p>
      </EmptyState>
    );
  }

  if (loading && !forceStopLoading) {
    return (
      <div className="ab-test-results-spinner" role="status" aria-live="polite">
        <Spinner accessibilityLabel="Loading test results" size="large" />
        <div className="ab-test-results-help-text">
          <Text as="p" variant="bodyMd" tone="subdued">
            Loading test results. This may take a moment for large datasets.
          </Text>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ab-test-results-section">
        <Banner title="Error loading results" tone="critical">
          {error}
        </Banner>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="ab-test-results-section">
        <Card>
          <Text as="p" variant="bodyMd" tone="subdued">
            No results available for this test yet. Please check back later.
          </Text>
        </Card>
      </div>
    );
  }

  // Defensive: Find winner variant safely
  const winnerVariant = Array.isArray(results.variants) ? results.variants.find((v: VariantResult) => v.is_winner) : undefined;

  // Defensive: Build table rows safely
  const rows = Array.isArray(results.variants) ? results.variants.map((variant: VariantResult) => [
    variant.description,
    variant.impressions,
    variant.conversions,
    `${variant.conversion_rate?.toFixed(2) ?? '0.00'}%`,
    `[${variant.confidence_interval?.[0]?.toFixed(2) ?? '0.00'}%, ${variant.confidence_interval?.[1]?.toFixed(2) ?? '0.00'}%]`,
    `$${variant.total_revenue?.toFixed(2) ?? '0.00'}`,
    `$${variant.revenue_per_visitor?.toFixed(2) ?? '0.00'}`,
    variant.is_winner ? 'Winner' : (
      <Button
        loading={declaringWinner === variant.id}
        onClick={() => setShowDeclareWinnerModal(variant.id)}
        disabled={!!winnerVariant}
        aria-label={`Declare ${variant.description} as winner`}
      >
        Declare Winner
      </Button>
    )
  ]) : [];

  // Defensive: Bayesian items
  const bayesianItems = results.bayesian_probabilities ? Object.entries(results.bayesian_probabilities).map(([key, value]) => ({
    term: `Prob. ${key}`,
    description: `${(value * 100).toFixed(2)}%`
  })) : [];

  // Defensive: Chart data
  const chartData = Array.isArray(results.variants) ? results.variants.map((v: VariantResult) => ({
    name: v.description,
    'Conversion Rate': v.conversion_rate,
    ci: v.confidence_interval,
  })) : [];

  return (
    <div className="ab-test-results-root" aria-label="A/B Test Results">
      <div className="ab-test-results">
        <Card>
          <LegacyStack distribution="equalSpacing" alignment="center">
            <Text variant="headingMd" as="h2">
              Test Results for: {results.test_name}
            </Text>
          </LegacyStack>

          <div className="ab-test-results-section">
            <Text as="p" variant="bodyMd" tone="subdued">
              Review the performance of each variant. Use the table and chart below to compare conversion rates, revenue, and statistical significance. You can declare a winner when ready.
            </Text>
          </div>

          {winnerVariant && (
            <Banner tone="success" title="Winner Declared">
              {`Variant ${winnerVariant.description} has been declared the winner.`}
            </Banner>
          )}

          <div className="ab-test-results-section">
            <LegacyStack distribution="fillEvenly" spacing="loose">
              <LegacyStack.Item>
                <DescriptionList items={[
                  { term: 'P-Value', description: (
                    <LegacyStack alignment="center" spacing="extraTight">
                      <span>{results.p_value.toFixed(4)}</span>
                      <Tooltip content="The p-value indicates the probability of observing the results if there were no real difference between variants. A value below 0.05 is typically considered statistically significant.">
                        <span>?</span>
                      </Tooltip>
                    </LegacyStack>
                  )},
                  { term: 'Effect Size', description: results.effect_size.toFixed(4) },
                  { term: 'Statistical Significance', description: results.is_significant ? 'Yes' : 'No' },
                ]} />
              </LegacyStack.Item>
              <LegacyStack.Item>
                <DescriptionList items={bayesianItems} />
              </LegacyStack.Item>
            </LegacyStack>
          </div>

          <div className="ab-test-results-section">
            <div className="ab-test-results-chart">
              <BarChart data={chartData} dataKey="Conversion Rate" xAxisKey="name" />
            </div>
          </div>

          <div className="ab-test-results-section ab-table-scroll">
            <DataTable
              columnContentTypes={['text', 'numeric', 'numeric', 'numeric', 'text', 'numeric', 'numeric', 'text']}
              headings={[
                'Variant',
                'Impressions',
                'Conversions',
                'Conv. Rate',
                'Confidence Interval',
                'Total Revenue',
                'RPV',
                'Actions'
              ]}
              rows={rows}
            />
          </div>

          {showDeclareWinnerModal && (
            <Modal
              open
              onClose={() => setShowDeclareWinnerModal(null)}
              title="Declare Winner"
              primaryAction={{
                content: 'Declare Winner',
                onAction: () => handleDeclareWinner(showDeclareWinnerModal),
                loading: declaringWinner === showDeclareWinnerModal,
              }}
              secondaryActions={[{ content: 'Cancel', onAction: () => setShowDeclareWinnerModal(null) }]}
            >
              <Modal.Section>
                <p>Are you sure you want to declare this variant as the winner? This action will end the test and redirect all traffic to the winning variant.</p>
              </Modal.Section>
            </Modal>
          )}

          {/* Segment winners could be displayed here */}
        </Card>
      </div>
    </div>
  );
}

export default ABTestResults;
