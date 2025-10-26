import { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Text,
  Spinner,
  Banner,
  ResourceList,
  ResourceItem,
  LegacyStack,
  Badge,
  Button,
  ButtonGroup,
  Modal,
  EmptyState,
  Toast,
  Frame,
} from '@shopify/polaris';
import { abTestingApi } from '../../../api/abTestingApi';
import './ExperimentManagement.css';

interface Experiment {
  id: number;
  name: string;
  status: 'DRAFT' | 'RUNNING' | 'PAUSED' | 'FINISHED' | 'ARCHIVED';
}

interface ExperimentManagementProps {
  forceStopLoading?: boolean;
}

const ExperimentManagement: React.FC<ExperimentManagementProps> = ({ forceStopLoading }) => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [showDeleteModal, setShowDeleteModal] = useState<number | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fetchExperiments = useCallback(async () => {
    setLoading(true);
    try {
      const response = await abTestingApi.getTests();
      setExperiments(response);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExperiments();
  }, [fetchExperiments]);

  const handleAction = useCallback(async (testId: number, action: 'start' | 'pause' | 'end' | 'delete') => {
    setActionLoading(prev => ({ ...prev, [`${testId}-${action}`]: true }));
    setError(null);
    try {
      switch (action) {
        case 'start':
          await abTestingApi.startTest(testId);
          setToastMessage('Test started successfully.');
          break;
        case 'pause':
          await abTestingApi.pauseTest(testId);
          setToastMessage('Test paused successfully.');
          break;
        case 'end':
          await abTestingApi.endTest(testId);
          setToastMessage('Test ended successfully.');
          break;
        case 'delete':
          await abTestingApi.deleteTest(testId);
          setToastMessage('Test deleted successfully.');
          setShowDeleteModal(null);
          break;
      }
      // Refresh the list after action
      fetchExperiments();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(prev => ({ ...prev, [`${testId}-${action}`]: false }));
    }
  }, [fetchExperiments]);


  if (loading && !forceStopLoading) {
    return (
      <Card>
        <LegacyStack alignment="center" distribution="center">
          <Spinner accessibilityLabel="Loading experiments" size="large" />
        </LegacyStack>
        <div className="experiment-management-help-text">
          <Text as="p" variant="bodyMd" tone="subdued">
            Loading your experiments. This may take a moment for large catalogs.
          </Text>
        </div>
      </Card>
    );
  }

  const statusBadgeTone = (status: Experiment['status']) => {
    switch (status) {
        case 'RUNNING': return 'success';
        case 'PAUSED': return 'attention';
        case 'FINISHED': return 'info';
        case 'ARCHIVED': return 'critical';
        default: return undefined;
    }
  }

  const renderActions = (item: Experiment) => {
    return (
        <ButtonGroup>
            {item.status === 'DRAFT' && <Button loading={actionLoading[`${item.id}-start`]} onClick={() => handleAction(item.id, 'start')}>Start</Button>}
            {item.status === 'RUNNING' && <Button loading={actionLoading[`${item.id}-pause`]} onClick={() => handleAction(item.id, 'pause')}>Pause</Button>}
            {item.status === 'PAUSED' && <Button loading={actionLoading[`${item.id}-start`]} onClick={() => handleAction(item.id, 'start')}>Resume</Button>}
            {item.status === 'RUNNING' && <Button loading={actionLoading[`${item.id}-end`]} onClick={() => handleAction(item.id, 'end')}>End</Button>}
            {(item.status === 'DRAFT' || item.status === 'FINISHED' || item.status === 'ARCHIVED') && <Button tone="critical" loading={actionLoading[`${item.id}-delete`]} onClick={() => setShowDeleteModal(item.id)}>Delete</Button>}
        </ButtonGroup>
    )
  }

  const toastMarkup = toastMessage ? (
    <Toast content={toastMessage} onDismiss={() => setToastMessage(null)} />
  ) : null;

  return (
    <div className="experiment-management-root">
      <Frame>
        {toastMarkup}
        <div className="experiment-management">
          <Card>
            <Text variant="headingMd" as="h2">
              Experiment Management
            </Text>
            <div className="experiment-management-section">
              <Text as="p" variant="bodyMd" tone="subdued">
                Manage all your A/B tests in one place. Start, pause, end, or delete experiments as needed. Use the actions to control the lifecycle of each test.
              </Text>
            </div>
            {error && (
              <Banner tone="critical">
                <Text as="p" variant="bodyMd" tone="subdued">{error}</Text>
              </Banner>
            )}
            {experiments.length === 0 ? (
              <EmptyState
                heading="No experiments to manage"
                image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
              >
                <Text as="p" variant="bodyMd" tone="subdued">
                  Create an A/B test to start managing your experiments.
                </Text>
              </EmptyState>
            ) : (
              <ResourceList
                resourceName={{ singular: 'experiment', plural: 'experiments' }}
                items={experiments}
                renderItem={(item) => {
                  const { id, name, status } = item;
                  return (
                    <ResourceItem
                      id={id.toString()}
                      onClick={() => {}}
                    >
                      <LegacyStack distribution="equalSpacing" alignment="center">
                        <LegacyStack.Item fill>
                          <Text variant="bodyMd" fontWeight="bold" as="h3">
                            {name}
                          </Text>
                        </LegacyStack.Item>
                        <LegacyStack.Item>
                          <Badge tone={statusBadgeTone(status)}>{status}</Badge>
                        </LegacyStack.Item>
                        <LegacyStack.Item>
                          {renderActions(item)}
                        </LegacyStack.Item>
                      </LegacyStack>
                    </ResourceItem>
                  );
                }}
              />
            )}
          </Card>
        </div>
        {showDeleteModal && (
          <Modal
            open
            onClose={() => setShowDeleteModal(null)}
            title="Delete Experiment"
            primaryAction={{
              content: 'Delete',
              destructive: true,
              onAction: () => handleAction(showDeleteModal, 'delete'),
              loading: actionLoading[`${showDeleteModal}-delete`],
            }}
            secondaryActions={[{ content: 'Cancel', onAction: () => setShowDeleteModal(null) }]}
          >
            <Modal.Section>
              <p>Are you sure you want to permanently delete this experiment? This action cannot be undone.</p>
            </Modal.Section>
          </Modal>
        )}
      </Frame>
    </div>
  );
};

export default ExperimentManagement;
