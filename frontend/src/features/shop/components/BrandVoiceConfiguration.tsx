import React, {  useState, useCallback } from 'react';
import { Card, FormLayout, TextField, Tag, Button, Banner, Spinner, Modal } from '@shopify/polaris';
import { useQuery, useMutation } from '@tanstack/react-query';
import { shopApi } from '../../../api/shopApi';
import type { BrandVoice } from '../../../api/shopApi';
import styles from './BrandVoiceConfiguration.module.css';

// Native file save utility (no dependency)
function saveFile(data: BlobPart, filename: string, mimeType = 'application/octet-stream') {
	const blob = new Blob([data], { type: mimeType });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	setTimeout(() => {
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}, 0);
}


interface BrandVoiceConfigurationProps {
	forceStopLoading?: boolean;
}

const defaultBrandVoice: BrandVoice = {
	tone_of_voice: '',
	vocabulary_preferences: { preferred: [], avoid: [] },
	industry_jargon: [],
	banned_words: [],
};

function validateBrandVoice(voice: BrandVoice) {
	if (!voice.tone_of_voice.trim()) return 'Tone of voice is required.';
	return '';
}

const BrandVoiceConfiguration: React.FC<BrandVoiceConfigurationProps> = ({ forceStopLoading }) => {
	const [brandVoice, setBrandVoice] = useState<BrandVoice>(defaultBrandVoice);
	const [editMode, setEditMode] = useState(false);
	const [error, setError] = useState('');
	const [success, setSuccess] = useState('');
	const [showImportModal, setShowImportModal] = useState(false);
	const [importJson, setImportJson] = useState('');
	const [aiSuggestion, setAiSuggestion] = useState<string | null>(null);

	//Fetch brand voice
			const {
				data,
				isLoading,
				error: fetchError,
				refetch,
			} = useQuery<BrandVoice>({
				queryKey: ['brandVoice'],
				queryFn: shopApi.getBrandVoice,
				retry: 1,
				staleTime: 5 * 60 * 1000,
			});

			React.useEffect(() => {
				if (
					data &&
					typeof data === 'object' &&
					'vocabulary_preferences' in data &&
					'tone_of_voice' in data &&
					'industry_jargon' in data &&
					'banned_words' in data
				) {
					setBrandVoice(data as BrandVoice);
				}
			}, [data]);


	// Save brand voice
	const saveMutation = useMutation({
		mutationFn: shopApi.saveBrandVoice,
		onSuccess: () => {
			setSuccess('Brand voice saved successfully!');
			setError('');
			setEditMode(false);
			refetch();
		},
		onError: () => setError('Failed to save brand voice.'),
	});

	// --- Advanced Features ---
	// AI Suggestion (mocked, can be replaced with real API)
	const handleAISuggest = useCallback(() => {
		setAiSuggestion('Try a tone like "Empowering, Innovative, and Trustworthy" for your brand.');
	}, []);

	// Export brand voice
	const handleExport = () => {
		saveFile(JSON.stringify(brandVoice, null, 2), 'brand-voice.json', 'application/json');
	};

	// Import brand voice
	const handleImport = () => {
		try {
			const parsed = JSON.parse(importJson);
			setBrandVoice(parsed);
			setShowImportModal(false);
			setEditMode(true);
			setError('');
		} catch {
			setError('Invalid JSON format.');
		}
	};

	// Reset to default
	const handleReset = () => {
		setBrandVoice(defaultBrandVoice);
		setEditMode(true);
		setError('');
	};

	// Handlers for fields
	const handleChange = (field: keyof BrandVoice, value: any) => {
		setBrandVoice((prev) => ({ ...prev, [field]: value }));
		setError('');
	};

	// Tag list handlers
	const handleTagAdd = (field: string, value: string) => {
		if (!value.trim()) return;
		setBrandVoice((prev) => {
			if (field === 'preferred' || field === 'avoid') {
				return {
					...prev,
					vocabulary_preferences: {
						...prev.vocabulary_preferences,
						[field]: [...prev.vocabulary_preferences[field], value.trim()],
					},
				};
			}
			return { ...prev, [field]: [...(prev[field as keyof BrandVoice] as string[]), value.trim()] };
		});
	};
	const handleTagRemove = (field: string, idx: number) => {
		setBrandVoice((prev) => {
			if (field === 'preferred' || field === 'avoid') {
				const arr = [...prev.vocabulary_preferences[field]];
				arr.splice(idx, 1);
				return {
					...prev,
					vocabulary_preferences: {
						...prev.vocabulary_preferences,
						[field]: arr,
					},
				};
			}
			const arr = [...(prev[field as keyof BrandVoice] as string[])];
			arr.splice(idx, 1);
			return { ...prev, [field]: arr };
		});
	};

	// Save handler
	const handleSave = () => {
		const validation = validateBrandVoice(brandVoice);
		if (validation) {
			setError(validation);
			return;
		}
		saveMutation.mutate(brandVoice);
	};

	// UI

			if (isLoading && !forceStopLoading) return <Spinner accessibilityLabel="Loading brand voice" size="large" />;

			return (
				<div className={styles.card}>
					<Card>
						<h2 className={styles.header}>Brand Voice Configuration</h2>
						<div className={styles.bannerSection}>
							{fetchError && (
								<Banner tone="critical">
									Failed to fetch brand voice. Please try again.
								</Banner>
							)}
							{error && <Banner tone="critical">{error}</Banner>}
							{success && <Banner tone="success" onDismiss={() => setSuccess('')}>{success}</Banner>}
							{aiSuggestion && <Banner tone="info" onDismiss={() => setAiSuggestion(null)}>{aiSuggestion}</Banner>}
						</div>
						<FormLayout>
							<div className={styles.section}>
								<TextField
									label="Tone of Voice"
									value={brandVoice.tone_of_voice}
									onChange={(v) => handleChange('tone_of_voice', v)}
									disabled={!editMode}
									helpText="E.g., Friendly, Professional, Playful, etc."
									autoComplete="off"
								/>
							</div>
							<div className={styles.stack}>
								<div className={styles.brandvoiceSection}>
									<label className={styles.label}>Preferred Vocabulary</label>
									<TagListWithInput
										tags={brandVoice.vocabulary_preferences.preferred}
										onAdd={(v) => handleTagAdd('preferred', v)}
										onRemove={(i) => handleTagRemove('preferred', i)}
										disabled={!editMode}
									/>
								</div>
								<div className={styles.brandvoiceSection}>
									<label className={styles.label}>Words to Avoid</label>
									<TagListWithInput
										tags={brandVoice.vocabulary_preferences.avoid}
										onAdd={(v) => handleTagAdd('avoid', v)}
										onRemove={(i) => handleTagRemove('avoid', i)}
										disabled={!editMode}
									/>
								</div>
							</div>
							<div className={styles.stack}>
								<div className={styles.brandvoiceSection}>
									<label className={styles.label}>Industry Jargon</label>
									<TagListWithInput
										tags={brandVoice.industry_jargon}
										onAdd={(v) => handleTagAdd('industry_jargon', v)}
										onRemove={(i) => handleTagRemove('industry_jargon', i)}
										disabled={!editMode}
									/>
								</div>
								<div className={styles.brandvoiceSection}>
									<label className={styles.label}>Banned Words</label>
									<TagListWithInput
										tags={brandVoice.banned_words}
										onAdd={(v) => handleTagAdd('banned_words', v)}
										onRemove={(i) => handleTagRemove('banned_words', i)}
										disabled={!editMode}
									/>
								</div>
							</div>
							<div className={styles.actions}>
								{!editMode ? (
									<Button onClick={() => setEditMode(true)} variant="primary">Edit</Button>
								) : (
									<Button onClick={handleSave} loading={saveMutation.isPending} variant="primary">Save</Button>
								)}
								<Button onClick={handleExport}>Export</Button>
								<Button onClick={() => setShowImportModal(true)}>Import</Button>
								<Button onClick={handleReset} tone="critical">Reset</Button>
								<Button onClick={handleAISuggest}>AI Suggestion</Button>
							</div>
						</FormLayout>
						<Modal
							open={showImportModal}
							onClose={() => setShowImportModal(false)}
							title="Import Brand Voice"
							primaryAction={{ content: 'Import', onAction: handleImport }}
							secondaryActions={[{ content: 'Cancel', onAction: () => setShowImportModal(false) }]}
						>
							<Modal.Section>
								<TextField
									label="Paste JSON here"
									value={importJson}
									onChange={setImportJson}
									multiline={6}
									autoComplete="off"
								/>
							</Modal.Section>
						</Modal>
					</Card>
				</div>
			);
};

// TagListWithInput: helper for tag input and display
const TagListWithInput: React.FC<{
	tags: string[];
	onAdd: (v: string) => void;
	onRemove: (idx: number) => void;
	disabled?: boolean;
}> = ({ tags, onAdd, onRemove, disabled }) => {
	const [input, setInput] = useState('');
	return (
		<div className={styles.tagListContainer}>
			<div className={styles.stack}>
						{Array.isArray(tags) && tags.map((tag, idx) => (
							<Tag key={tag + idx} onRemove={disabled ? undefined : () => onRemove(idx)}>{tag}</Tag>
						))}
			</div>
			<TextField
				label="Add"
				value={input}
				onChange={setInput}
				onBlur={() => {
					if (input.trim()) { onAdd(input); setInput(''); }
				}}
				disabled={disabled}
				autoComplete="off"
			/>
		</div>
	);
};

export default BrandVoiceConfiguration;
