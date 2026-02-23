import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthContext } from './AuthContext';
import LoadingScreen from './components/LoadingScreen';


const ProtectedRoute = ({ children }) => {
    const { user, loading } = useContext(AuthContext);
    const location = useLocation();

    if (loading) {
        return <LoadingScreen />;
    }

    if (!user || !user.is_authenticated) {
        // Save where they were trying to go
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return children;
};

export default ProtectedRoute;