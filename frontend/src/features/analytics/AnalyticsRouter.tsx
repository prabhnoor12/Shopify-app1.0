import { Routes, Route, Navigate } from 'react-router-dom';
import AnalyticsPage from './pages/AnalyticsPage';

const AnalyticsRouter = () => (
  <Routes>
    <Route path="" element={<AnalyticsPage />} />
    <Route path="*" element={<Navigate to="/analytics" replace />} />
  </Routes>
);

export default AnalyticsRouter;
