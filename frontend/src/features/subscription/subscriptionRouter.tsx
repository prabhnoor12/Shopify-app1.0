import { Routes, Route, Navigate } from 'react-router-dom';
import SubscriptionPage from './pages/subscriptionPage';

const SubscriptionRouter: React.FC = () => (
  <Routes>
    <Route path="" element={<SubscriptionPage />} />
    <Route path="*" element={<Navigate to="/subscription" replace />} />
  </Routes>
);

export default SubscriptionRouter;
