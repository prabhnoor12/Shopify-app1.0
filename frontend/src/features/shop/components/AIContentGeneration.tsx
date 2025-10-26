

import React, { useState, useEffect } from 'react';

interface AIContentGenerationProps {
	forceStopLoading: boolean;
	generationResult: GenerationResultData | null;
	setGenerationResult: (result: GenerationResultData | null) => void;
	selectedProduct: string;
	setSelectedProduct: (id: string) => void;
		setError?: (error: string | null) => void;
}
import GenerationResult from './GenerationResult';
import { translateWithDeepL, SUPPORTED_LANGUAGES } from './LanguageTranslation';
import AsyncVocabSelect from './AsyncVocabSelect';
import AsyncCollectionSelect from './AsyncCollectionSelect';
import './AIContentGeneration.css';
import {
  Card,
  Tabs,
  Spinner,
  Banner,
  Button,
  Select,
  TextField,
  Layout,
} from '@shopify/polaris';
import axios from 'axios';

type Product = {
	id: string;
	title: string;
	image?: string;
};

export type GenerationResultData = {
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
};

const TABS = [
	{ id: 'details', content: 'From Details' },
	{ id: 'image', content: 'From Image' },
	{ id: 'url', content: 'From URL' },
];

const AIContentGeneration: React.FC<AIContentGenerationProps> = ({ forceStopLoading, generationResult, setGenerationResult, selectedProduct, setSelectedProduct, setError }) => {
	const [products, setProducts] = useState<Product[]>([]);
	// selectedProduct and setSelectedProduct come from props
	const [selectedProductTitle, setSelectedProductTitle] = useState<string>('');
    const [tabIndex, setTabIndex] = useState(0);
	const [inputs, setInputs] = useState({
		tone: '',
		length: '',
		style: '',
		keywords: '',
		image: '',
		url: '',
		targetAudience: '',
		brandGuidelines: '',
		language: 'EN' as import('./LanguageTranslation').SupportedLanguage, // Use DeepL language codes
	});
	const [variantCount, setVariantCount] = useState<number>(1);
	const [translatedResult, setTranslatedResult] = useState<GenerationResultData | null>(null);
	const [translating, setTranslating] = useState(false);
	const [loading, setLoading] = useState(false);
	const [syncing, setSyncing] = useState(false);
	const [syncSuccess, setSyncSuccess] = useState<string | null>(null);

	useEffect(() => {
		// Fetch products from backend
		const fetchProducts = async () => {
			try {
				setLoading(true);
				const res = await axios.get('/api/shopify/products');
				setProducts(res.data.products);
				setLoading(false);
			} catch (err) {
			if (setError) setError('Failed to fetch products.');
				setLoading(false);
			}
		};
		fetchProducts();
	}, []);

	// Removed unused handleInputChange function

		const handleGenerate = async () => {
		if (setError) setError(null);
			setGenerationResult(null);
			setTranslatedResult(null);
			setLoading(true);
			try {
				let endpoint = '';
				let payload: any = {
					productId: selectedProduct,
					tone: inputs.tone,
					length: inputs.length,
					style: inputs.style,
					keywords: inputs.keywords,
					targetAudience: inputs.targetAudience,
					brandGuidelines: inputs.brandGuidelines,
					language: inputs.language,
					variantCount,
				};
				const tabId = TABS[tabIndex].id;
				if (tabId === 'details') {
					endpoint = '/api/ai/generate-from-details';
				} else if (tabId === 'image') {
					endpoint = '/api/ai/generate-from-image';
					payload.image = inputs.image;
				} else if (tabId === 'url') {
					endpoint = '/api/ai/generate-from-url';
					payload.url = inputs.url;
				}
				const response = await axios.post(endpoint, payload);
				const resultData: GenerationResultData = response.data.result;
				setGenerationResult(resultData);
				// Translate generated content if language is not English
				if (inputs.language !== 'EN' && resultData?.descriptions?.length) {
					setTranslating(true);
					try {
						const translatedDescriptions = await Promise.all(
							resultData.descriptions.map((desc: string) =>
								translateWithDeepL({ text: desc, targetLang: inputs.language as import('./LanguageTranslation').SupportedLanguage, apiKey: '' })
							)
						);
						setTranslatedResult({
							...resultData,
							descriptions: translatedDescriptions.map((t: import('./LanguageTranslation').TranslationResult) => t.translated),
						});
					} catch (err: any) {
						if (setError) setError('Translation failed: ' + (err?.message || 'Unknown error'));
						setTranslatedResult(null);
					} finally {
						setTranslating(false);
					}
				} else {
					setTranslatedResult(null);
				}
			} catch (err: any) {
				if (setError) setError(err?.response?.data?.message || 'Failed to generate content.');
			} finally {
				setLoading(false);
			}
		};

		// (Removed duplicate translation logic)
		const handleSyncToShopify = async () => {
			if (!generationResult || !selectedProduct) return;
			setSyncing(true);
			setSyncSuccess(null);
		if (setError) setError(null);
			try {
				// Use first description for sync, or let user pick in future
				const syncPayload = {
					product_id: selectedProduct,
					description: generationResult.descriptions[0],
					meta_title: generationResult.meta_title,
					meta_description: generationResult.meta_description,
					keywords: generationResult.keywords,
				};
				await axios.post('/api/shopify/sync-product-content', syncPayload);
				setSyncSuccess('Content synced to Shopify successfully!');
			} catch (err: any) {
				if (setError) setError(err?.response?.data?.message || 'Failed to sync to Shopify.');
			} finally {
				setSyncing(false);
			}
		};

		return (
			<Card>
				<div className="ai-content-title">AI Product Content Generation</div>
				{syncSuccess && <Banner title="Success" tone="success">{syncSuccess}</Banner>}
						{loading && !forceStopLoading && (
							<Spinner size="large" accessibilityLabel="Loading" />
						)}
				<Layout>
					<Layout.Section>
						<AsyncCollectionSelect
							label="Product"
							value={selectedProduct}
							onChange={(id) => {
								setSelectedProduct(id);
								const found = products.find(p => p.id === id);
								setSelectedProductTitle(found ? found.title : '');
							}}
							fetchUrl="/api/shopify/products"
						/>
						{selectedProductTitle && (
							<div className="ai-selected-product-title">Selected product: {selectedProductTitle}</div>
						)}
					</Layout.Section>
				</Layout>
				<Tabs
					tabs={TABS}
					selected={tabIndex}
					onSelect={setTabIndex}
				/>
				<div className="ai-content-inputs">
					<TextField
						label="Tone"
						name="tone"
						value={inputs.tone}
						onChange={(val) => setInputs((prev) => ({ ...prev, tone: val }))}
						placeholder="e.g. Friendly, Professional"
						autoComplete="off"
					/>
					<TextField
						label="Length"
						name="length"
						value={inputs.length}
						onChange={(val) => setInputs((prev) => ({ ...prev, length: val }))}
						placeholder="e.g. Short, Medium, Long"
						autoComplete="off"
					/>
					<TextField
						label="Style"
						name="style"
						value={inputs.style}
						onChange={(val) => setInputs((prev) => ({ ...prev, style: val }))}
						placeholder="e.g. Conversational, Technical"
						autoComplete="off"
					/>
					<AsyncVocabSelect
						label="Keywords"
						value={inputs.keywords}
						onChange={(val) => setInputs((prev) => ({ ...prev, keywords: val }))}
						onSelect={(item) => setInputs((prev) => ({ ...prev, keywords: item }))}
						fetchUrl="/api/vocab/keywords"
					/>
					<TextField
						label="Target Audience"
						name="targetAudience"
						value={inputs.targetAudience}
						onChange={(val) => setInputs((prev) => ({ ...prev, targetAudience: val }))}
						placeholder="e.g. Millennials, Tech Enthusiasts"
						autoComplete="off"
					/>
					<TextField
						label="Brand Guidelines"
						name="brandGuidelines"
						value={inputs.brandGuidelines}
						onChange={(val) => setInputs((prev) => ({ ...prev, brandGuidelines: val }))}
						placeholder="e.g. Use playful tone, avoid jargon"
						autoComplete="off"
					/>
					<Select
						label="Language"
						options={SUPPORTED_LANGUAGES.map(lang => ({ label: lang.name, value: lang.code }))}
						value={inputs.language}
						onChange={(val) => setInputs((prev) => ({ ...prev, language: val as import('./LanguageTranslation').SupportedLanguage }))}
					/>
					<TextField
						label="Number of Variants"
						type="number"
						min={1}
						max={10}
						value={variantCount.toString()}
						onChange={val => setVariantCount(Math.max(1, Math.min(10, Number(val))))}
						placeholder="e.g. 3"
						autoComplete="off"
					/>
					{TABS[tabIndex].id === 'image' && (
						<TextField
							label="Image URL"
							name="image"
							value={inputs.image}
							onChange={(val) => setInputs((prev) => ({ ...prev, image: val }))}
							placeholder="Paste image URL"
							autoComplete="off"
						/>
					)}
					{TABS[tabIndex].id === 'url' && (
						<TextField
							label="Product URL"
							name="url"
							value={inputs.url}
							onChange={(val) => setInputs((prev) => ({ ...prev, url: val }))}
							placeholder="Paste product URL"
							autoComplete="off"
						/>
					)}
				</div>
				<div className="ai-content-generate-btn">
					<Button
						onClick={handleGenerate}
						disabled={loading || !selectedProduct}
						variant="primary"
					>
						Generate Content
					</Button>
				</div>
					{(translatedResult || generationResult) && (
						<>
							<GenerationResult
								result={translatedResult || generationResult}
								selectedProduct={selectedProduct}
								setError={setError}
							/>
							<div className="ai-content-sync-btn">
								<Button
									onClick={handleSyncToShopify}
									loading={syncing}
									disabled={syncing}
									variant="primary"
								>
									Sync to Shopify
								</Button>
							</div>
							{translating && (
								<Spinner size="small" accessibilityLabel="Translating..." />
							)}
						</>
					)}
			</Card>
	);
};

export default AIContentGeneration;
