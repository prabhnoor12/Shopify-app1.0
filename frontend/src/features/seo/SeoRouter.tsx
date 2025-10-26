import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import SEOPage from  './pages/SEOPage'

const SeoRouter: React.FC = () => {
  return (
    <Routes>
  <Route path="" element={<SEOPage />} />
  <Route path="url" element={<SEOPage initialTab={0} />} />
  <Route path="score" element={<SEOPage initialTab={1} />} />
  <Route path="title" element={<SEOPage initialTab={2} />} />
  <Route path="meta" element={<SEOPage initialTab={3} />} />
  <Route path="readability" element={<SEOPage initialTab={4} />} />
  <Route path="keywords" element={<SEOPage initialTab={5} />} />
  <Route path="headings" element={<SEOPage initialTab={6} />} />
  <Route path="images" element={<SEOPage initialTab={7} />} />
  <Route path="links" element={<SEOPage initialTab={8} />} />
  <Route path="ai" element={<SEOPage initialTab={9} />} />
      <Route path="*" element={<Navigate to="/seo" replace />} />
    </Routes>
  );
};

export default SeoRouter;
