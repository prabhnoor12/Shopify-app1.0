import React, { useState, useCallback, useEffect } from 'react';
import {
  Page,
  Layout,
  Card,
  FormLayout,
  TextField,
  Select,
  ChoiceList,
  RangeSlider,
  Text,
  Icon,
  Banner,
  BlockStack,
  InlineStack,
  ProgressBar,
  Spinner,
  Thumbnail,
} from '@shopify/polaris';
import { useNavigate } from 'react-router-dom';
import { QuestionCircleIcon } from '@shopify/polaris-icons';
import { shopApi } from '../../../api/shopApi';
import { abTestingApi } from '../../../api/abTestingApi';

// Box is not in Polaris v6+, so use div with className or create a Box component if needed
const Box: React.FC<any> = ({ children, padding, paddingBlockEnd, paddingInlineStart, as = 'div', ...props }) => {
  const style: React.CSSProperties = {};
  if (padding) style.padding = typeof padding === 'string' ? padding : `${padding}px`;
  if (paddingBlockEnd) style.paddingBlockEnd = typeof paddingBlockEnd === 'string' ? paddingBlockEnd : `${paddingBlockEnd}px`;
  if (paddingInlineStart) style.paddingInlineStart = typeof paddingInlineStart === 'string' ? paddingInlineStart : `${paddingInlineStart}px`;
  const Tag = as;
  return <Tag style={style} {...props}>{children}</Tag>;
};

// Types
interface Product {
  id: string;
  name: string;
  image: string;
}

interface Variation {
  id: string;
  name: string;
  productId: string;
  trafficSplit: number;
}

interface ABTestData {
  name: string;
  testType: string;
  variations: Variation[];
}
const TOTAL_STEPS = 3;

interface ABTestCreationWizardProps {
  forceStopLoading?: boolean;
}

const ABTestCreationWizard: React.FC<ABTestCreationWizardProps> = ({ forceStopLoading }) => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(true);
  const [productsError, setProductsError] = useState<string | null>(null);
  const [testData, setTestData] = useState<ABTestData>({
    name: '',
    testType: 'product_page',
    variations: [
      { id: 'A', name: 'Variation A', productId: '', trafficSplit: 50 },
      { id: 'B', name: 'Variation B', productId: '', trafficSplit: 50 },
    ],
  });
  const [submitting, setSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [submissionSuccess, setSubmissionSuccess] = useState(false);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setProductsLoading(true);
        const fetchedProducts: any[] = await shopApi.getProducts();
        const formattedProducts = fetchedProducts.map((p: any) => ({
            id: p.id.toString(),
            name: p.title,
            image: p.image ? p.image.src : '' // Remove placeholder, show nothing if no image
        }));
        setProducts(formattedProducts);
      } catch (error) {
        setProductsError('Failed to load products. Please try again.');
        console.error(error);
      } finally {
        setProductsLoading(false);
      }
    };

    fetchProducts();
  }, []);

  const handleInputChange = useCallback((field: keyof ABTestData) => (value: string) => {
    setTestData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleVariationProductChange = (index: number) => (productId: string) => {
    const newVariations = [...testData.variations];
    newVariations[index].productId = productId;
    setTestData(prev => ({ ...prev, variations: newVariations }));
  };

  const handleTrafficSplitChange = (value: number) => {
    const newVariations = [...testData.variations];
    newVariations[0].trafficSplit = value;
    newVariations[1].trafficSplit = 100 - value;
    setTestData(prev => ({ ...prev, variations: newVariations }));
  };

  const nextStep = () => {
    if (currentStep < TOTAL_STEPS) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const renderProductOption = (productId: string) => {
    const product = products.find(p => p.id === productId);
    if (!product) return null;
    return (
      <InlineStack gap="400" blockAlign="center">
        <Thumbnail source={product.image} alt={product.name} />
        <Text variant="bodyMd" as="p">{product.name}</Text>
      </InlineStack>
    );
  };

  const isNextDisabled = (): boolean => {
    switch (currentStep) {
      case 1:
        return !testData.name;
      case 2:
        return testData.variations.some(v => !v.productId);
      default:
        return false;
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setSubmissionError(null);
    try {
      await abTestingApi.createTest(testData);
      setSubmissionSuccess(true);
    } catch (error) {
      setSubmissionError('Failed to create A/B test. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const renderStepContent = () => {
    if (productsLoading && !forceStopLoading) {
      return (
        <div className="wizard-spinner-container">
          <InlineStack align="center" blockAlign="center">
            <Spinner accessibilityLabel="Loading products" size="large" />
          </InlineStack>
          <div className="wizard-help-text">
            <Text as="p" variant="bodyMd" tone="subdued">
              Loading your products. This may take a moment for large catalogs.
            </Text>
          </div>
        </div>
      );
    }

    if (productsError) {
      return <Banner title="Error loading products" tone="critical">{productsError}</Banner>;
    }

    if (products.length === 0) {
      return (
        <Banner title="No products available" tone="warning">
          <p>You must add products to your store before creating an A/B test. <br />
          <span className="wizard-help-text">Go to your Shopify admin to add products, then refresh this page.</span></p>
        </Banner>
      );
    }

    switch (currentStep) {
      case 1:
        return (
          <div className="wizard-content">
            <div className="wizard-help-text">
              <Text as="p" variant="bodyMd" tone="subdued">
                Name your A/B test and select the type of test you want to run. You can test product pages now; more types coming soon!
              </Text>
            </div>
            <FormLayout>
              <TextField
                label="A/B Test Name"
                value={testData.name}
                onChange={handleInputChange('name')}
                autoComplete="off"
                placeholder="e.g., Homepage Headline Test"
                helpText="Give your test a descriptive name so you can easily identify it later."
              />
                <ChoiceList
                title="Test Type"
                choices={[
                  { label: 'Product Page', value: 'product_page' },
                  { label: 'Collection Page (Coming Soon)', value: 'collection_page', disabled: true },
                  { label: 'Homepage (Coming Soon)', value: 'homepage', disabled: true },
                ]}
                selected={[testData.testType]}
                onChange={(value) => {
                  // ChoiceList onChange typically provides string[]; be defensive in case of unexpected shapes
                  const selected = Array.isArray(value) ? value[0] : (value as unknown as string);
                  handleInputChange('testType')(selected ?? '');
                }}
              />
            </FormLayout>
          </div>
        );
      case 2:
        return (
          <div className="wizard-content">
            <div className="wizard-help-text">
              <Text as="p" variant="bodyMd" tone="subdued">
                Select the products you want to test. Each variation should have a different product.
              </Text>
            </div>
            <FormLayout>
              {testData.variations.map((variation, index) => (
                <Select
                  key={variation.id}
                  label={`Variation ${variation.id}`}
                  options={[
                    { label: 'Select a product', value: '' },
                    ...products.map(p => ({ label: p.name, value: p.id }))
                  ]}
                  onChange={handleVariationProductChange(index)}
                  value={variation.productId}
                  placeholder="Select a product for this variation"
                  helpText="Choose a product for this variation. Each variation should have a unique product."
                />
              ))}
            </FormLayout>
          </div>
        );
      case 3:
        return (
          <div className="wizard-content">
            <div className="wizard-help-text">
              <Text as="p" variant="bodyMd" tone="subdued">
                Adjust the traffic split between your variations. Review your selections before creating the test.
              </Text>
            </div>
            <BlockStack gap="400">
              {testData.variations.map((variation) => (
                <Card key={variation.id}>
                  <Box padding="400">
                    <Text variant="headingMd" as="h3">{variation.name}</Text>
                    {renderProductOption(variation.productId)}
                  </Box>
                </Card>
              ))}
              <Card>
                <Box padding="400">
                  <FormLayout>
                    <FormLayout.Group>
                      <Text variant="bodyMd" as="p">
                        Traffic Split
                        <Box as="span" paddingInlineStart="200">
                          <Icon source={QuestionCircleIcon} tone="base" />
                        </Box>
                      </Text>
                    </FormLayout.Group>
                    <RangeSlider
                      output
                      label="Traffic split between variations"
                      labelHidden
                      value={testData.variations[0].trafficSplit}
                      onChange={handleTrafficSplitChange}
                      min={0}
                      max={100}
                      step={1}
                    />
                    <InlineStack align="space-between" blockAlign="center">
                      <Text variant="bodyMd" as="p" tone="subdued">{testData.variations[0].trafficSplit}%</Text>
                      <Text variant="bodyMd" as="p" tone="subdued">{testData.variations[1].trafficSplit}%</Text>
                    </InlineStack>
                  </FormLayout>
                </Box>
              </Card>
            </BlockStack>
          </div>
        );
      default:
        return null;
    }
  };

  const renderSummary = () => (
    <BlockStack gap="400">
      <Card>
        <Box padding="400">
          <Text variant="headingMd" as="h2">Test Details</Text>
          <p><strong>Name:</strong> {testData.name}</p>
          <p><strong>Type:</strong> {testData.testType.replace('_', ' ')}</p>
        </Box>
      </Card>
      <Card>
        <Box padding="400">
          <Text variant="headingMd" as="h2">Variations & Traffic Split</Text>
          {testData.variations.map(v => (
            <div key={v.id}>
              <p><strong>{v.name}:</strong> {renderProductOption(v.productId)} ({v.trafficSplit}%)</p>
            </div>
          ))}
        </Box>
      </Card>
    </BlockStack>
  );

  if (submissionSuccess) {
    return (
      <Page
        title="A/B Test Created"
        primaryAction={{ content: 'View All Tests', onAction: () => navigate('/ab-tests') }}
      >
        <Layout>
          <Layout.Section>
            <div className="wizard-success-message">
              <InlineStack gap="200" align="center" blockAlign="center">
                <span className="wizard-success-check">✔️</span>
                <Text variant="headingLg" as="h2">
                  Success!
                </Text>
              </InlineStack>
              <p className="wizard-success-text">Your new A/B test has been created successfully.</p>
            </div>
            {renderSummary()}
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <div className="ab-test-creation-wizard-root">
      <div className="ab-test-creation-wizard">
        <Page
          title="Create New A/B Test"
          backAction={{ content: 'A/B Tests', onAction: () => navigate('/ab-tests') }}
          primaryAction={currentStep < TOTAL_STEPS ? { content: 'Next', onAction: nextStep, disabled: isNextDisabled() } : { content: 'Create Test', onAction: handleSubmit, loading: submitting }}
          secondaryActions={currentStep > 1 ? [{ content: 'Previous', onAction: prevStep }] : []}
        >
          <Layout>
            <Layout.Section>
              <Box paddingBlockEnd="400">
                <ProgressBar progress={(currentStep / TOTAL_STEPS) * 100} />
                <div className="wizard-steps">
                  {[1, 2, 3].map((step) => (
                    <div key={step} className={`step${currentStep === step ? ' active' : ''}`}>
                      <div className="step-number">{step}</div>
                      <span>
                        {step === 1 && 'Details'}
                        {step === 2 && 'Variations'}
                        {step === 3 && 'Summary'}
                      </span>
                    </div>
                  ))}
                </div>
                {submissionError && <Banner title="Error" tone="critical">{submissionError}</Banner>}
                <hr className="wizard-section-divider" />
                {renderStepContent()}
              </Box>
            </Layout.Section>
            <Layout.Section variant="oneThird">
              <Card>
                <Box padding="400">
                  <Text variant="headingMd" as="h2">Summary</Text>
                  {renderSummary()}
                </Box>
              </Card>
            </Layout.Section>
          </Layout>
        </Page>
      </div>
    </div>
  );
};

export default ABTestCreationWizard;
