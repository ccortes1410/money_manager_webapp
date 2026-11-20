import { useState, lazy, Suspense } from 'react';
import AuthProvider from './AuthProvider';
import { ToastProvider } from './components/Toast/ToastContext';
import { Routes, Route, Outlet } from 'react-router-dom';
import Sidebar from './components/Sidebar/Sidebar';
import ProtectedRoute from './ProtectedRoute';
import LoadingScreen from './components/LoadingScreen';
import ErrorBoundary from './components/ErrorBoundary';
import "./App.css";


const LandingPage = lazy(() => import("./components/LandingPage/LandingPage"));
const Login = lazy(() => import("./components/Auth/Login"));
const Register = lazy(() => import("./components/Auth/Register"));
const ForgotPassword = lazy(() => import("./components/Auth/ForgotPassword"));
const ResetPassword = lazy(() => import("./components/Auth/ResetPassword"));
const Dashboard = lazy(() => import("./components/Dashboard/Dashboard"));
const Transactions = lazy(() => import("./components/Transactions/Transactions"));
const Budgets = lazy(() => import("./components/Budgets/Budgets"));
const Subscriptions = lazy(() => import("./components/Subscriptions/Subscriptions"));
const Income = lazy(() => import("./components/Income/Income"));
const Friends = lazy(() => import("./components/Friends/Friends"));
const SharedBudgets = lazy(() => import("./components/SharedBudgets/SharedBudgets"));
const SharedBudgetDetail = lazy(() => import("./components/SharedBudgets/SharedBudgetDetail"));
const Settings = lazy(() => import("./components/Settings/Settings"));
const NotFound = lazy(() => import("./components/NotFound/NotFound"));


function AppLayout({ collapsed, toggleSidebar }) {
   
    return (
            <div className="app-layout">
                <Sidebar collapsed={collapsed} onToggle={toggleSidebar} />
                <main className={`main-content ${collapsed ? "collapsed" : ""}`}>
                    <Outlet />
                </main>
            </div>
    );
}

function App() {
    const [ collapsed, setCollapsed ] = useState(() => {
        if (typeof window !== "undefined" && window.innerWidth <= 768) {
            return true;
        }
        return JSON.parse(localStorage.getItem("sidebarCollapsed")) || false;
    });

    const toggleSidebar = () => {
        setCollapsed((prev) => {
            localStorage.setItem("sidebarCollapsed", JSON.stringify(!prev));
        return !prev;
        });
    };

    return (
        <ErrorBoundary>
            <AuthProvider>
                <ToastProvider>
                    
                        <Suspense fallback={<LoadingScreen />}>
                            <div id="main-content">
                                <Routes>
                                    {/* Public Routes */}
                                    <Route path="/" element={<LandingPage />} />
                                    <Route path="/login" element={<Login />} />
                                    <Route path="/register" element={<Register />} />
                                    <Route path="/forgot-password" element={<ForgotPassword />} />
                                    <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />

                                    {/* Protected Routes */}
                                    <Route element={<AppLayout collapsed={collapsed} toggleSidebar={toggleSidebar} />}>
                                    
                                    <Route path="/dashboard" element={
                                        <ProtectedRoute>
                                            <div className="app-container">
                                                <Dashboard />
                                            </div>
                                        </ProtectedRoute>
                                    } />
                                    <Route path="/transactions" element={
                                        <ProtectedRoute>
                                            <div className="app-container">
                                                <Transactions />
                                            </div>
                                        </ProtectedRoute>
                                    } />
                                    <Route path="/budgets" element={
                                        <ProtectedRoute>
                                            <div className="app-container">
                                                <Budgets />
                                            </div>
                                        </ProtectedRoute>
                                    } />
                                    <Route path="/subscriptions" element={
                                        <ProtectedRoute>
                                            <div className="app-container">
                                                <Subscriptions />
                                            </div>
                                        </ProtectedRoute>
                                    } />
                                    <Route path="/income" element={
                                        <ProtectedRoute>
                                            <div className="app-container">
                                                <Income />
                                            </div>
                                        </ProtectedRoute>
                                    } />
                                    <Route path="/friends" element={
                                        <ProtectedRoute>
                                            <div className="app-container">
                                                <Friends />
                                            </div>
                                        </ProtectedRoute>
                                    } />
                                    <Route path="/shared-budgets" element={
                                        <ProtectedRoute>
                                            <div className="app-container">
                                                <SharedBudgets />
                                            </div>
                                        </ProtectedRoute>
                                    } />
                                    <Route path="/shared-budgets/:id" element={
                                        <ProtectedRoute>
                                            <div className="app-container">
                                                <SharedBudgetDetail />
                                            </div>
                                        </ProtectedRoute>
                                    } />
                                    <Route path="/settings" element={
                                        <ProtectedRoute>
                                            <div className="app-container">
                                                <Settings />
                                            </div>
                                        </ProtectedRoute>
                                    } />
                                    </Route>

                                    {/* 404 */}
                                    <Route path="*" element={<NotFound />} />
                                </Routes>
                            </div>
                        </Suspense>
                    
                </ToastProvider>
            </AuthProvider>
        </ErrorBoundary>
    );
}

export default App;