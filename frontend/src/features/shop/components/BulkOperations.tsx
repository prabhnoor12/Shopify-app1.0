import React, { useState } from 'react';
import {
  Card,
  Button,
  Banner,
  Spinner,
  List,
  TextContainer,
  LegacyStack,
  Checkbox,
  ProgressBar,
} from '@shopify/polaris';
import { shopApi } from '../../../api/shopApi';
import './BulkOperations.css';
import AsyncCollectionSelect from './AsyncCollectionSelect';
import AsyncVocabSelect from './AsyncVocabSelect';
import type { GenerationResultData } from './AIContentGeneration';

interface Product {
  id: string;
  title: string;
  description?: string;
  [key: string]: any;
}

interface ExportError {
  id: string;
  error: string;
}

interface BulkOperationsProps {
  generationResult?: GenerationResultData | null;
  setGenerationResult?: (result: GenerationResultData | null) => void;
  selectedProduct?: string;
  setSelectedProduct?: (id: string) => void;
  setError?: (error: string | null) => void;
}

const BulkOperations: React.FC<BulkOperationsProps> = ({ setError }) => {
  const [step, setStep] = useState<'idle' | 'importing' | 'imported' | 'generating' | 'generated' | 'exporting' | 'exported' | 'error'>('idle');
  const [products, setProducts] = useState<Product[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [error, _setError] = useState<string | null>(null); // use prop setError instead
  const [exportedCount, setExportedCount] = useState<number>(0);
  const [exportErrors, setExportErrors] = useState<ExportError[]>([]);
  const [progress, setProgress] = useState<number>(0);
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [selectedVocab, setSelectedVocab] = useState<string>('');

  // Import products from Shopify
  const importProducts = async () => {
    setStep('importing');
  if (setError) setError(null);
    setProgress(0);
    try {
      let url = '/api/products';
      if (selectedCollection) {
        url += `?collection=${encodeURIComponent(selectedCollection)}`;
      }
      const result = await fetch(url).then(res => res.json());
      setProducts(result);
      setSelected(new Set(result.map((p: Product) => p.id)));
      setStep('imported');
    } catch (e: any) {
  if (setError) setError(e.message || 'Failed to import products.');
      setStep('error');
    }
  };

  // Select/deselect products
  const toggleProduct = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };
  const selectAll = () => setSelected(new Set(products.map((p) => p.id)));
  const deselectAll = () => setSelected(new Set());

  // Generate descriptions in bulk
  const generateDescriptions = async () => {
    setStep('generating');
  if (setError) setError(null);
    setProgress(0);
    try {
      const ids = Array.from(selected);
      let payload: any = { product_ids: ids };
      if (selectedVocab) payload.vocab = selectedVocab;
      const result = await shopApi.bulkGenerateDescriptions(payload);
      setProducts((prev) =>
        prev.map((p) => {
          const found = result.find((r: any) => r.id === p.id);
          return found ? { ...p, description: found.description } : p;
        })
      );
      setProgress(100);
      setStep('generated');
    } catch (e: any) {
  if (setError) setError(e.message || 'Failed to generate descriptions.');
      setStep('error');
    }
  };

  // Export products with new descriptions back to Shopify
  const exportProducts = async () => {
    setStep('exporting');
  if (setError) setError(null);
    setProgress(0);
    setExportErrors([]);
    try {
      const toExport = products.filter((p) => selected.has(p.id));
      let successCount = 0;
      const failed: ExportError[] = [];
      for (let i = 0; i < toExport.length; i++) {
        try {
          let payload: any = { products: [{ id: toExport[i].id, description: toExport[i].description }] };
          if (selectedVocab) payload.vocab = selectedVocab;
          await shopApi.bulkSaveDescriptions(payload);
          successCount++;
        } catch (e: any) {
          failed.push({ id: toExport[i].id, error: e.message || 'Export failed' });
        }
        setProgress(Math.round(((i + 1) / toExport.length) * 100));
      }
      setExportedCount(successCount);
      setExportErrors(failed);
      setStep('exported');
    } catch (e: any) {
  if (setError) setError(e.message || 'Failed to export products.');
      setStep('error');
    }
  };

  // Retry failed exports
  const retryFailedExports = async () => {
    setStep('exporting');
  if (setError) setError(null);
    setProgress(0);
    try {
      let successCount = exportedCount;
      const failed: ExportError[] = [];
      for (let i = 0; i < exportErrors.length; i++) {
        const prod = products.find((p) => p.id === exportErrors[i].id);
        if (!prod) continue;
        try {
          await shopApi.bulkSaveDescriptions({ products: [{ id: prod.id, description: prod.description }] });
          successCount++;
        } catch (e: any) {
          failed.push({ id: prod.id, error: e.message || 'Export failed' });
        }
        setProgress(Math.round(((i + 1) / exportErrors.length) * 100));
      }
      setExportedCount(successCount);
      setExportErrors(failed);
      setStep('exported');
    } catch (e: any) {
  if (setError) setError(e.message || 'Failed to retry exports.');
      setStep('error');
    }
  };

  const reset = () => {
    setStep('idle');
    setProducts([]);
    setExportedCount(0);
    setExportErrors([]);
    setSelected(new Set());
    setProgress(0);
  if (setError) setError(null);
  };

  return (
    <div className="bulk-operations">
      <Card>
        <LegacyStack vertical>
          <TextContainer>
            <h2>Bulk Operations</h2>
            <p>
              Import products from Shopify, select which to process, generate descriptions in bulk, and export them back to Shopify. Track progress and retry failed exports.
            </p>
          </TextContainer>

          {error && <Banner tone="critical">{error}</Banner>}

          {step === 'idle' && (
            <Button onClick={importProducts}>Import Products from Shopify</Button>
          )}

          {step === 'importing' && <Spinner accessibilityLabel="Importing products" size="large" />}

          {step === 'imported' && (
            <>
              <Banner tone="success">Imported {Array.isArray(products) ? products.length : 0} products.</Banner>
              <div className="button-group">
                <Button onClick={selectAll} size="slim">Select All</Button>
                <Button onClick={deselectAll} size="slim">Deselect All</Button>
              </div>
              <div className="bulk-operations-selectors">
                <AsyncCollectionSelect
                  label="Select Collection"
                  value={selectedCollection}
                  onChange={setSelectedCollection}
                  fetchUrl="/api/collections"
                />
                <AsyncVocabSelect
                  label="Select Vocabulary"
                  value={selectedVocab}
                  onChange={setSelectedVocab}
                  onSelect={setSelectedVocab}
                  fetchUrl="/api/vocabularies"
                />
              </div>
              <div className="bulk-operations-list">
                <List type="bullet">
                  {Array.isArray(products) && products.map((p) => (
                    <List.Item key={p.id}>
                      <Checkbox
                        label={p.title}
                        checked={selected.has(p.id)}
                        onChange={() => toggleProduct(p.id)}
                      />
                    </List.Item>
                  ))}
                </List>
              </div>
              <Button onClick={generateDescriptions} disabled={selected.size === 0}>Generate Descriptions in Bulk</Button>
            </>
          )}

          {step === 'generating' && (
            <>
              <Spinner accessibilityLabel="Generating descriptions" size="large" />
              <ProgressBar progress={progress} size="small" />
            </>
          )}

          {step === 'generated' && (
            <>
              <Banner tone="success">Descriptions generated for all selected products.</Banner>
              <div className="bulk-operations-list">
                <List type="bullet">
                  {Array.isArray(products) && products.filter((p) => selected.has(p.id)).map((p) => (
                    <List.Item key={p.id}>{p.title}: {p.description}</List.Item>
                  ))}
                </List>
              </div>
              <Button onClick={exportProducts}>Export Products to Shopify</Button>
            </>
          )}

          {step === 'exporting' && (
            <>
              <Spinner accessibilityLabel="Exporting products" size="large" />
              <ProgressBar progress={progress} size="small" />
            </>
          )}

          {step === 'exported' && (
            <>
              <Banner tone="success">Exported {exportedCount} products to Shopify!</Banner>
              {Array.isArray(exportErrors) && exportErrors.length > 0 && (
                <Banner tone="critical" title="Some products failed to export:">
                  <List type="bullet">
                    {exportErrors.map((err) => (
                      <List.Item key={err.id}>Product {err.id}: {err.error}</List.Item>
                    ))}
                  </List>
                  <Button onClick={retryFailedExports} size="slim">Retry Failed Exports</Button>
                </Banner>
              )}
              <Button onClick={reset}>Start Over</Button>
            </>
          )}
        </LegacyStack>
      </Card>
    </div>
  );
};

export default BulkOperations;
