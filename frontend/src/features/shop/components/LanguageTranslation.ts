// List of supported languages with names
export const SUPPORTED_LANGUAGES: { code: SupportedLanguage; name: string }[] = [
	{ code: 'EN', name: 'English' },
	{ code: 'DE', name: 'German' },
	{ code: 'FR', name: 'French' },
	{ code: 'ES', name: 'Spanish' },
	{ code: 'IT', name: 'Italian' },
	{ code: 'NL', name: 'Dutch' },
	{ code: 'PL', name: 'Polish' },
	{ code: 'RU', name: 'Russian' },
	{ code: 'JA', name: 'Japanese' },
	{ code: 'ZH', name: 'Chinese' },
];

// Simple in-memory cache for translations
const translationCache = new Map<string, TranslationResult>();

/**
 * Detects the language of a given text using DeepL API.
 */
export async function detectLanguage(text: string, apiKey?: string): Promise<string> {
	const url = 'https://api-free.deepl.com/v2/translate';
	const deeplApiKey = apiKey || import.meta.env.DEEPL_API_KEY;
	if (!deeplApiKey) throw new Error('DeepL API key is missing.');
	const params = new URLSearchParams({
		auth_key: deeplApiKey,
		text,
		target_lang: 'EN', // Use English as dummy target
	});
	try {
		const response: AxiosResponse = await axios.post(url, params, {
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
		});
		const data = response.data;
		if (!data.translations || !data.translations[0]) {
			throw new Error('No detection result from DeepL');
		}
		return data.translations[0].detected_source_language;
	} catch (error: any) {
		throw new Error(error?.response?.data?.message || error.message || 'Language detection failed');
	}
}

/**
 * Batch translate multiple texts to a target language.
 */
export async function batchTranslateWithDeepL({ texts, targetLang, apiKey }: { texts: string[]; targetLang: SupportedLanguage; apiKey?: string }): Promise<TranslationResult[]> {
	const url = 'https://api-free.deepl.com/v2/translate';
	const deeplApiKey = apiKey || import.meta.env.DEEPL_API_KEY;
	if (!deeplApiKey) throw new Error('DeepL API key is missing.');
	const params = new URLSearchParams({
		auth_key: deeplApiKey,
		target_lang: targetLang,
	});
	(texts || []).forEach(text => params.append('text', text));
	try {
		const response: AxiosResponse = await axios.post(url, params, {
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
		});
		const data = response.data;
		if (!data.translations) throw new Error('No translations returned from DeepL');
		return data.translations.map((t: any, i: number) => ({
			original: texts[i],
			translated: t.text,
			detected_source_language: t.detected_source_language,
		}));
	} catch (error: any) {
		throw new Error(error?.response?.data?.message || error.message || 'Batch translation failed');
	}
}
import axios from 'axios';
import type { AxiosResponse } from 'axios';

export type SupportedLanguage =
	| 'EN' // English
	| 'DE' // German
	| 'FR' // French
	| 'ES' // Spanish
	| 'IT' // Italian
	| 'NL' // Dutch
	| 'PL' // Polish
	| 'RU' // Russian
	| 'JA' // Japanese
	| 'ZH'; // Chinese

export interface TranslationResult {
	original: string;
	translated: string;
	detected_source_language: string;
}

export interface DeepLTranslateOptions {
	text: string;
	targetLang: SupportedLanguage;
	apiKey: string;
}

/**
 * Translates text using DeepL API.
 * Throws error on failure. Returns translation result.
 */
export async function translateWithDeepL({ text, targetLang, apiKey }: DeepLTranslateOptions): Promise<TranslationResult> {
			const cacheKey = `${text}|${targetLang}`;
			if (translationCache.has(cacheKey)) {
				return translationCache.get(cacheKey)!;
			}
			const url = 'https://api-free.deepl.com/v2/translate';
			const deeplApiKey = apiKey || import.meta.env.DEEPL_API_KEY;
			if (!deeplApiKey) {
				throw new Error('DeepL API key is missing. Please set DEEPL_API_KEY in your .env file.');
			}
			const params = new URLSearchParams({
				auth_key: deeplApiKey,
				text,
				target_lang: targetLang,
			});
			try {
				const response: AxiosResponse = await axios.post(url, params, {
					headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
				});
				const data = response.data;
				if (!data.translations || !data.translations[0]) {
					throw new Error('No translation returned from DeepL');
				}
				const result: TranslationResult = {
					original: text,
					translated: data.translations[0].text,
					detected_source_language: data.translations[0].detected_source_language,
				};
				translationCache.set(cacheKey, result);
				return result;
			} catch (error: any) {
				throw new Error(error?.response?.data?.message || error.message || 'Translation failed');
			}
}
