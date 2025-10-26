import React from 'react';
import { Routes, Route, useParams } from 'react-router-dom';

import ProductDetail from './components/ProductDetail';
import ProductForm from './components/ProductForm';
import ProductPage from './pages/ProductPage';
import ProductList from './components/ProductList';
import ProductAltTextGenerator from './components/ProductAltTextGenerator';
import ProductContentAudit from './components/ProductContentAudit';
import ProductDeleteDialog from './components/ProductDeleteDialog';
import ProductPerformanceAnalysis from './components/ProductPerformanceAnalysis';
import ProductRecommendations from './components/ProductRecommendations';
import ProductShopifySync from './components/ProductShopifySync';

const ProductDetailWrapper: React.FC = () => {
  const { id } = useParams();
  if (!id) return <div>Product ID not found.</div>;
  return <ProductDetail productId={id} />;
};

const ProductRouter: React.FC = () => {
  return (
    <Routes>
      <Route path="" element={<ProductPage />} />
      <Route path=":id" element={<ProductDetailWrapper />} />
      <Route path="add" element={<ProductForm />} />
      <Route path="list" element={<ProductList />} />
      <Route path="alt-text" element={<ProductAltTextGenerator />} />
      <Route path="audit" element={<ProductContentAudit />} />
      <Route path="delete/:id" element={<ProductDeleteDialog productId="1" productName="Mock T-Shirt" onClose={() => {}} />} />
      <Route path="performance" element={<ProductPerformanceAnalysis />} />
      <Route path="recommendations" element={<ProductRecommendations />} />
      <Route path="shopify-sync" element={<ProductShopifySync />} />
      {/* Default route: redirect to product page */}
      <Route path="*" element={<ProductPage />} />
    </Routes>
  );
};

export default ProductRouter;
