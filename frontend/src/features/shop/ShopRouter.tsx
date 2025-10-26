import { Routes, Route, Navigate } from 'react-router-dom';
import ShopPage from './pages/ShopPage';

const ShopRouter = () => (
  <Routes>
    <Route path="" element={<ShopPage />} />
    <Route path="ai-content-generation" element={<ShopPage initialTab={0} />} />
    <Route path="brand-voice" element={<ShopPage initialTab={1} />} />
    <Route path="bulk-operations" element={<ShopPage initialTab={2} />} />
    <Route path="gdpr" element={<ShopPage initialTab={3} />} />
    <Route path="*" element={<Navigate to="/shop" replace />} />
  </Routes>
);

export default ShopRouter;
