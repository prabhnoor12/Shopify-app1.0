import { Routes, Route, Navigate } from 'react-router-dom';
import UserPage from './page/UserPage';


const UserRouter = () => (
  <Routes>
    <Route path="" element={<UserPage />} />

    <Route path="*" element={<Navigate to="/users" replace />} />
  </Routes>
);

export default UserRouter;
