import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';

const DashboardRouter = () => (
  <Routes>
    <Route path="" element={<DashboardPage />} />
    <Route path="*" element={<Navigate to="/dashboard" replace />} />
  </Routes>
);

export default DashboardRouter;
