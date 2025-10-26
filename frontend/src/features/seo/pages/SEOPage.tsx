import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './SeoPage.module.css';

import SEOUrlAnalyzer from '../components/SEOUrlAnalyzer';
import SEOScoreCard from '../components/SEOScoreCard';
import SEOTitleAnalysis from '../components/SEOTitleAnalysis';
import SEOMetaDescriptionAnalysis from '../components/SEOMetaDescriptionAnalysis';
import SEOReadability from '../components/SEOReadability';
import SEOKeywordAnalysis from '../components/SEOKeywordAnalysis';
import SEOHeadingAnalysis from '../components/SEOHeadingAnalysis';
import SEOImageAnalysis from '../components/SEOImageAnalysis';
import SEOLinkAnalysis from '../components/SEOLinkAnalysis';
import SEOAISuggestions from '../components/SEOAISuggestions';

type Props = {
	initialTab?: number;
};

const tabDefinitions = [
	{ key: '', label: 'Overview', component: () => <SEOScoreCard /> },
	{ key: 'url', label: 'URL', component: () => <SEOUrlAnalyzer /> },
	{ key: 'score', label: 'Score', component: () => <SEOScoreCard /> },
	{ key: 'title', label: 'Title', component: () => <SEOTitleAnalysis /> },
	{ key: 'meta', label: 'Meta', component: () => <SEOMetaDescriptionAnalysis /> },
	{ key: 'readability', label: 'Readability', component: () => <SEOReadability /> },
	{ key: 'keywords', label: 'Keywords', component: () => <SEOKeywordAnalysis /> },
	{ key: 'headings', label: 'Headings', component: () => <SEOHeadingAnalysis /> },
	{ key: 'images', label: 'Images', component: () => <SEOImageAnalysis /> },
	{ key: 'links', label: 'Links', component: () => <SEOLinkAnalysis /> },
	{ key: 'ai', label: 'AI Suggestions', component: () => <SEOAISuggestions /> },
];

const SEOPage: React.FC<Props> = ({ initialTab = 0 }) => {
	const navigate = useNavigate();
	const safeInitial = Math.min(Math.max(initialTab, 0), tabDefinitions.length - 1);
	const [activeIndex, setActiveIndex] = useState<number>(safeInitial);

	const activeTab = tabDefinitions[activeIndex];

	const TabContent = useMemo(() => activeTab.component, [activeTab]);

	const handleTabClick = (index: number) => {
		setActiveIndex(index);
		const key = tabDefinitions[index].key;
		// navigate to sub-route so deep links and bookmarking work
		navigate(key ? `/seo/${key}` : '/seo');
	};

	return (
		<div className={styles['seo-dashboard']}>
			<h1>SEO Toolkit</h1>

			<div className={styles['seo-tabs']} role="tablist">
				{tabDefinitions.map((t, i) => (
					<button
						key={t.key || 'overview'}
						className={
							styles['seo-tab'] + (i === activeIndex ? ' ' + styles['seo-tab-active'] : '')
						}
						role="tab"
						id={`seo-tab-${i}`}
						aria-selected={i === activeIndex ? 'true' : 'false'}
						tabIndex={i === activeIndex ? 0 : -1}
						aria-controls={`seo-tabpanel-${i}`}
						onClick={() => handleTabClick(i)}
					>
						{t.label}
					</button>
				))}
			</div>

			<div
				className={styles['seo-tab-content']}
				role="tabpanel"
				id={`seo-tabpanel-${activeIndex}`}
				aria-labelledby={`seo-tab-${activeIndex}`}
			>
				<TabContent />
			</div>
		</div>
	);
};

export default SEOPage;
