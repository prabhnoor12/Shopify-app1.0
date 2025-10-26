import { Routes, Route, Navigate } from 'react-router-dom';
import ABTestingPage from './pages/ABTestingPage';

const ABTestingRouter = () => (
  <Routes>
    <Route path="" element={<ABTestingPage />} />
    <Route path="dashboard" element={<ABTestingPage initialTab={0} />} />
    <Route path="create" element={<ABTestingPage initialTab={1} />} />
    <Route path="results/:testId" element={<ABTestingPage initialTab={2} />} />
    <Route path="ai-recommendations" element={<ABTestingPage initialTab={3} />} />
    <Route path="experiment-management" element={<ABTestingPage initialTab={4} />} />
    <Route path="*" element={<Navigate to="/ab-testing" replace />} />
  </Routes>
);

export default ABTestingRouter;
