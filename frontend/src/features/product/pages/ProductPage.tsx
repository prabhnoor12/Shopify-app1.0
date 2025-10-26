import React, { useState } from 'react';
import './ProductPage.css';
import ProductList from '../components/ProductList';
import ProductAltTextGenerator from '../components/ProductAltTextGenerator';
import ProductForm from '../components/ProductForm';
import ProductContentAudit from '../components/ProductContentAudit';
import ProductPerformanceAnalysis from '../components/ProductPerformanceAnalysis';
import ProductRecommendations from '../components/ProductRecommendations';
import ProductShopifySync from '../components/ProductShopifySync';

const TABS = [
	{ key: 'list', label: 'Product List', component: <ProductList /> },
	{ key: 'alt-text', label: 'Alt Text Generator', component: <ProductAltTextGenerator /> },
	{ key: 'form', label: 'Product Form', component: <ProductForm /> },
	{ key: 'audit', label: 'Content Audit', component: <ProductContentAudit /> },
	{ key: 'performance', label: 'Performance Analysis', component: <ProductPerformanceAnalysis /> },
	{ key: 'recommendations', label: 'Recommendations', component: <ProductRecommendations /> },
	{ key: 'shopify-sync', label: 'Shopify Sync', component: <ProductShopifySync /> },
];

const ProductPage: React.FC = () => {
	const [activeTab, setActiveTab] = useState('list');

	return (
		<div className="product-page">
			<h1>Product Page</h1>
			<div className="product-tabs">
				{TABS.map(tab => (
					<button
						key={tab.key}
						className={`product-tab-btn${activeTab === tab.key ? ' active' : ''}`}
						onClick={() => setActiveTab(tab.key)}
					>
						{tab.label}
					</button>
				))}
			</div>
			<div className="product-tab-content">
				{TABS.find(tab => tab.key === activeTab)?.component}
			</div>
		</div>
	);
};

export default ProductPage;
