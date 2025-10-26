import { Routes, Route, Navigate } from 'react-router-dom';
import UsagePage from './pages/UsagePage';

const UsageRouter: React.FC = () => (
  <Routes>
    <Route path="" element={<UsagePage />} />
    <Route path="*" element={<Navigate to="/usage" replace />} />
  </Routes>
);

export default UsageRouter;
