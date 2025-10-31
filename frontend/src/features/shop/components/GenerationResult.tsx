// src/features/shop/components/GenerationResult.tsx
import { useState, useCallback } from 'react';
import {
  Card,
  Text,
  Button,
  LegacyStack,
  TextContainer,
  Toast,
  Frame,
  Box,
  List,
  Collapsible,
  Icon,
  Banner,
  Spinner,
  Modal,
} from '@shopify/polaris';
import { CheckSmallIcon } from '@shopify/polaris-icons';
import { shopApi } from '../../../api/shopApi';
import './GenerationResult.css';

interface GenerationResultData {
  descriptions: string[];
  keywords: string[];
  meta_title: string;
  meta_description: string;
  seo_analysis?: {
    clarity?: string;
    emotional_tone?: string;
    keyword_density?: { keyword: string; density: string }[];
  };
  seo_suggestions?: string[];
}

interface GenerationResultProps {
  result: GenerationResultData | null;
  selectedProduct: string;
  setError?: (error: string | null) => void;
}

const GenerationResult = ({ result, selectedProduct, setError }: GenerationResultProps) => {
  const [saving, setSaving] = useState<{ [key: number]: boolean }>({});
  const [showToast, setShowToast] = useState(false);
  const [saved, setSaved] = useState<{ [key: number]: boolean }>({});
  const [isSeoAnalysisOpen, setIsSeoAnalysisOpen] = useState(false);
  const [featureInput, setFeatureInput] = useState<{ [key: number]: string }>({});
  const [benefit, setBenefit] = useState<{ [key: number]: string }>({});
  const [benefitLoading, setBenefitLoading] = useState<{ [key: number]: boolean }>({});
  const [benefitError, setBenefitError] = useState<{ [key: number]: string | null }>({});
  const [modalOpen, setModalOpen] = useState<{ [key: number]: boolean }>({});

  const handleSaveDescription = useCallback(async (description: string, index: number) => {
    setSaving(prev => ({ ...prev, [index]: true }));
  if (setError) setError(null);
    try {
      await shopApi.saveDescription({ product_id: selectedProduct, new_description: description });
      setShowToast(true);
      setSaved(prev => ({ ...prev, [index]: true }));
    } catch (e: any) {
  if (setError) setError(e.message);
    } finally {
      setSaving(prev => ({ ...prev, [index]: false }));
    }
  }, [selectedProduct, setError]);

  const handleFeatureToBenefit = async (feature: string, index: number) => {
    setBenefitLoading(prev => ({ ...prev, [index]: true }));
    setBenefitError(prev => ({ ...prev, [index]: null }));
    try {
      const res = await shopApi.transformFeatureToBenefit({ feature });
      setBenefit(prev => ({ ...prev, [index]: res.benefit }));
    } catch (e: any) {
      setBenefitError(prev => ({ ...prev, [index]: e.message || 'Failed to convert feature.' }));
    } finally {
      setBenefitLoading(prev => ({ ...prev, [index]: false }));
    }
  };

  const toastMarkup = showToast ? (
    <Toast content="Description saved" onDismiss={() => setShowToast(false)} />
  ) : null;

  if (!result) {
    return (
      <Box padding="400">
        <TextContainer>
          <Text as="p" tone="subdued">
            Your generated content and SEO analysis will appear here.
          </Text>
        </TextContainer>
      </Box>
    );
  }

  return (
    <Frame>
      <div className="ai-content-results">
        <LegacyStack vertical>
          <Text variant="headingMd" as="h3">Generated Content Variants</Text>
          {Array.isArray(result.descriptions) && result.descriptions.map((desc, i) => {
            // Basic SEO analysis (very simple)
            const basicClarity = desc.length > 120 ? 'Good' : 'Needs more detail';
            const basicKeywordDensity = Array.isArray(result.keywords) && result.keywords.length > 0 ? result.keywords.map(k => ({ keyword: k, density: `${((desc.match(new RegExp(k, 'gi')) || []).length / desc.split(' ').length * 100).toFixed(1)}%` })) : [];
            return (
              <Card key={i}>
                  <div className="ai-description-center">
                    <Text as="p" variant="bodyMd">{desc}</Text>
                  </div>
                  <div className="ai-basic-seo">
                    <Text as="span" tone="subdued">Clarity: {basicClarity}</Text>
                    {Array.isArray(basicKeywordDensity) && basicKeywordDensity.length > 0 && (
                        <span className="ai-keyword-density">
                        <Text as="span" tone="subdued">
                          Keyword Density: {basicKeywordDensity.map(kd => `${kd.keyword}: ${kd.density}`).join(', ')}
                        </Text>
                      </span>
                    )}
                  </div>
                  <div className="save-button-container">
                    {saved[i] ? (
                      <LegacyStack alignment="center" spacing="tight">
                        <Icon source={CheckSmallIcon} tone="success" />
                        <Text as="span" tone="success">Saved</Text>
                      </LegacyStack>
                    ) : (
                      <Button
                        onClick={() => handleSaveDescription(desc, i)}
                        loading={saving[i]}
                        disabled={Object.values(saving).some(s => s)}
                      >
                        Save this version
                      </Button>
                    )}
                  </div>
                  <div className="feature-to-benefit">
                    <Button
                      icon={CheckSmallIcon}
                      size="slim"
                      onClick={() => setModalOpen(prev => ({ ...prev, [i]: true }))}
                    >
                      Feature → Benefit
                    </Button>
                    <Modal
                      open={!!modalOpen[i]}
                      onClose={() => setModalOpen(prev => ({ ...prev, [i]: false }))}
                      title="Convert Feature to Benefit"
                      primaryAction={{
                        content: benefitLoading[i] ? 'Converting...' : 'Convert',
                        onAction: () => handleFeatureToBenefit(featureInput[i] || '', i),
                        disabled: !featureInput[i] || benefitLoading[i],
                      }}
                      secondaryActions={[
                        { content: 'Close', onAction: () => setModalOpen(prev => ({ ...prev, [i]: false })) },
                      ]}
                    >
                      <Box paddingBlockStart="200">
                        <TextContainer>
                          <Text as="span">Paste a product feature below to see a customer-focused benefit:</Text>
                          <textarea
                            className="feature-benefit-textarea"
                            value={featureInput[i] || ''}
                            onChange={e => setFeatureInput(prev => ({ ...prev, [i]: (e.target as HTMLTextAreaElement).value }))}
                            placeholder="E.g. '100% organic cotton'"
                            autoFocus
                          />
                          {benefitLoading[i] && <Spinner size="small" />}
                          {benefit[i] && (
                            <Banner tone="success" title="Benefit">
                              {benefit[i]}
                            </Banner>
                          )}
                          {benefitError[i] && (
                            <Banner tone="critical">{benefitError[i]}</Banner>
                          )}
                        </TextContainer>
                      </Box>
                    </Modal>
                  </div>
                {/* End of removed Card.Section */}
              </Card>
            );
          })}

          <Card>
            <Text variant="headingMd" as="h3">SEO Analysis</Text>
            <Box paddingBlockStart="200">
              <LegacyStack vertical spacing="tight">
                <p><strong>Meta Title:</strong> {result.meta_title}</p>
                <p><strong>Meta Description:</strong> {result.meta_description}</p>
                <p><strong>Keywords:</strong> {result.keywords.join(', ')}</p>
              </LegacyStack>
            </Box>

            {result.seo_analysis && (
              <Box paddingBlockStart="400">
                <Button
                  onClick={() => setIsSeoAnalysisOpen(!isSeoAnalysisOpen)}
                  ariaExpanded={isSeoAnalysisOpen}
                  ariaControls="seo-analysis-content"
                >
                  {isSeoAnalysisOpen ? 'Hide' : 'Show'} Detailed Analysis
                </Button>
                <Collapsible
                  open={isSeoAnalysisOpen}
                  id="seo-analysis-content"
                  transition={{ duration: '300ms', timingFunction: 'ease-in-out' }}
                >
                  <Box paddingBlockStart="400">
                    <LegacyStack vertical>
                      {result.seo_analysis.clarity && <p><strong>Clarity Score:</strong> {result.seo_analysis.clarity}</p>}
                      {result.seo_analysis.emotional_tone && <p><strong>Emotional Tone:</strong> {result.seo_analysis.emotional_tone}</p>}
                      {result.seo_analysis.keyword_density && result.seo_analysis.keyword_density.length > 0 && (
                        <>
                          <Text as="p" fontWeight="bold">Keyword Density:</Text>
                          <List type="bullet">
                            {result.seo_analysis.keyword_density.map(kd => (
                              <List.Item key={kd.keyword}>
                                "{kd.keyword}": {kd.density}
                              </List.Item>
                            ))}
                          </List>
                        </>
                      )}
                    </LegacyStack>
                  </Box>
                </Collapsible>
              </Box>
            )}

            {result.seo_suggestions && result.seo_suggestions.length > 0 && (
              <Box paddingBlockStart="400">
                <Text as="p" fontWeight="bold">Suggestions for Improvement:</Text>
                <List type="bullet">
                  {result.seo_suggestions.map((suggestion, i) => (
                    <List.Item key={i}>{suggestion}</List.Item>
                  ))}
                </List>
              </Box>
            )}
          </Card>
        </LegacyStack>
        {toastMarkup}
      </div>
    </Frame>
  );
};

export default GenerationResult;
