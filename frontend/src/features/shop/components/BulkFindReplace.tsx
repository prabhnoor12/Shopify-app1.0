import { useCallback, useReducer } from 'react';
import {
  Card,
  Text,
  Form,
  FormLayout,
  TextField,
  Button,
  Spinner,
  Banner,
  List,
  Modal,
  TextContainer,
  LegacyStack,
} from '@shopify/polaris';
import AsyncCollectionSelect from './AsyncCollectionSelect';
import { shopApi } from '../../../api/shopApi';
import './BulkFindReplace.css';

interface BulkReplaceResult {
  updated_products: string[];
  errors: { product_id: string; error: string }[];
  total_matches: number;
}

type State = {
  status: 'idle' | 'confirming' | 'processing' | 'success' | 'error';
  findText: string;
  replaceText: string;
  collectionId: string;
  result: BulkReplaceResult | null;
  error: string | null;
};

type Action =
  | { type: 'SET_FIELD'; field: 'findText' | 'replaceText' | 'collectionId'; value: string }
  | { type: 'START_CONFIRMATION' }
  | { type: 'CANCEL_CONFIRMATION' }
  | { type: 'START_PROCESSING' }
  | { type: 'SET_SUCCESS'; payload: BulkReplaceResult }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'RESET' };

const initialState: State = {
  status: 'idle',
  findText: '',
  replaceText: '',
  collectionId: '',
  result: null,
  error: null,
};

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'SET_FIELD':
      return { ...state, [action.field]: action.value };
    case 'START_CONFIRMATION':
      if (!state.findText) {
        return { ...state, status: 'error', error: '"Find" text cannot be empty.' };
      }
      if (state.findText === state.replaceText) {
        return { ...state, status: 'error', error: '"Find" and "Replace" text cannot be the same.' };
      }
      return { ...state, status: 'confirming', error: null };
    case 'CANCEL_CONFIRMATION':
      return { ...state, status: 'idle' };
    case 'START_PROCESSING':
      return { ...state, status: 'processing', result: null, error: null };
    case 'SET_SUCCESS':
      return { ...state, status: 'success', result: action.payload };
    case 'SET_ERROR':
      return { ...state, status: 'error', error: action.payload };
    case 'RESET':
      return { ...initialState };
    default:
      return state;
  }
};

interface BulkFindReplaceProps {
  forceStopLoading?: boolean;
}

const BulkFindReplace: React.FC<BulkFindReplaceProps> = ({ forceStopLoading }) => {
  const [state, dispatch] = useReducer(reducer, initialState);
  const { status, findText, replaceText, collectionId, result, error } = state;

  const handleBulkReplace = useCallback(async () => {
    dispatch({ type: 'START_PROCESSING' });
    try {
      const response = await shopApi.bulkFindReplace({
        find_text: findText,
        replace_text: replaceText,
        collection_id: collectionId || null,
      });
      dispatch({ type: 'SET_SUCCESS', payload: response });
    } catch (err: any) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
    }
  }, [findText, replaceText, collectionId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    dispatch({ type: 'START_CONFIRMATION' });
  };

  const isProcessing = status === 'processing';

  return (
  <div className="bulk-find-replace">
      <Card>
        <LegacyStack vertical>
          <TextContainer>
            <Text variant="headingMd" as="h2">
              Bulk Find & Replace
            </Text>
            <p>This action will find and replace text across product descriptions. This can be a powerful tool, but use it with caution as changes cannot be easily undone.</p>
          </TextContainer>

          {error && <Banner tone="critical" onDismiss={() => dispatch({ type: 'SET_ERROR', payload: null })}>{error}</Banner>}

          <Form onSubmit={handleSubmit}>
            <FormLayout>
              <TextField
                label="Find Text"
                value={findText}
                onChange={(value) => dispatch({ type: 'SET_FIELD', field: 'findText', value })}
                autoComplete="off"
                helpText="Case-insensitive, whole word matching."
                disabled={isProcessing}
              />
              <TextField
                label="Replace With"
                value={replaceText}
                onChange={(value) => dispatch({ type: 'SET_FIELD', field: 'replaceText', value })}
                autoComplete="off"
                disabled={isProcessing}
              />
              <AsyncCollectionSelect
                label="Collection (Optional)"
                value={collectionId}
                onChange={(value) => dispatch({ type: 'SET_FIELD', field: 'collectionId', value })}
                fetchUrl="/api/collections"
              />
              <Button submit loading={isProcessing} variant="primary">
                Start Bulk Replace
              </Button>
            </FormLayout>
          </Form>

          {isProcessing && !forceStopLoading && <Spinner accessibilityLabel="Processing bulk replace" size="large" />}

          {status === 'success' && result && (
            <div className="bulk-find-replace-result">
              <Banner tone="success" title="Bulk Replace Completed" onDismiss={() => dispatch({ type: 'RESET' })}>
                <p>Found {result.total_matches} matches and updated {result.updated_products.length} products.</p>
              </Banner>
              {result.errors.length > 0 && (
                <Banner tone="critical" title="Errors">
                  <List type="bullet">
                    {result.errors.map((err, i) => (
                      <List.Item key={i}>
                        Product {err.product_id}: {err.error}
                      </List.Item>
                    ))}
                  </List>
                </Banner>
              )}
            </div>
          )}
        </LegacyStack>
      </Card>
      <Modal
        open={status === 'confirming'}
        onClose={() => dispatch({ type: 'CANCEL_CONFIRMATION' })}
        title="Confirm Bulk Replace"
        primaryAction={{
          content: 'Confirm & Replace',
          onAction: handleBulkReplace,
          destructive: true,
        }}
        secondaryActions={[
          {
            content: 'Cancel',
            onAction: () => dispatch({ type: 'CANCEL_CONFIRMATION' }),
          },
        ]}
      >
        <Modal.Section>
          <TextContainer>
            <p>You are about to perform a bulk find and replace with the following details:</p>
            <List type="bullet">
              <List.Item>Find: <strong>{findText}</strong></List.Item>
              <List.Item>Replace with: <strong>{replaceText || '(nothing)'}</strong></List.Item>
              {collectionId && <List.Item>Within collection: <strong>{collectionId}</strong></List.Item>}
            </List>
            <p>This action cannot be undone. Are you sure you want to proceed?</p>
          </TextContainer>
        </Modal.Section>
      </Modal>
    </div>
  );
};

export default BulkFindReplace;
