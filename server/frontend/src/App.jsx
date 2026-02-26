import { useState, useEffect, lazy, Suspense } from 'react';
// import { AuthContext } from './AuthContext';
import AuthProvider from './AuthProvider';
import { ToastProvider } from './components/Toast/ToastContext';
// import Login from './components/Auth/Login';
import { Routes, Route, Outlet } from 'react-router-dom';
// import LandingPage from './components/LandingPage/LandingPage';
// import Register from './components/Auth/Register';
// import Dashboard from './components/Dashboard/Dashboard';
// import Transactions from './components/Transactions/Transactions';
// import Budget from './components/Budgets/Budget';
// import Budgets from './components/Budgets/Budgets';
// import Subscriptions from './components/Subscriptions/Subscriptions';
import Sidebar from './components/Sidebar/Sidebar';
// import Income from './components/Income/Income';
// import Friends from './components/Friends/Friends'
import ProtectedRoute from './ProtectedRoute';
import LoadingScreen from './components/LoadingScreen';
import ErrorBoundary from './components/ErrorBoundary';
// import SharedBudgets from './components/SharedBudgets/SharedBudgets';
// import SharedBudgetDetail from './components/SharedBudgets/SharedBudgetDetail';
import "./App.css";


const LandingPage = lazy(() => import("./components/LandingPage/LandingPage"));
const Login = lazy(() => import("./components/Auth/Login"));
const Register = lazy(() => import("./components/Auth/Register"));
const Dashboard = lazy(() => import("./components/Dashboard/Dashboard"));
const Transactions = lazy(() => import("./components/Transactions/Transactions"));
const Budgets = lazy(() => import("./components/Budgets/Budgets"));
const Subscriptions = lazy(() => import("./components/Subscriptions/Subscriptions"));
const Income = lazy(() => import("./components/Income/Income"));
const Friends = lazy(() => import("./components/Friends/Friends"))
const SharedBudgets = lazy(() => import("./components/SharedBudgets/SharedBudgets"));
const NotFound = lazy(() => import("./components/NotFound/NotFound"));

// import Savings from './components/Savings/Savings';
// import Friends from './components/Friends/Friends';


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
    const [ collapsed, setCollapsed ] = useState(
        () => JSON.parse(localStorage.getItem("sidebarCollapsed")) || false
    );
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch("/djangoapp/user", {
            credentials: "include",
        })
        .then(res => {
            if (!res.ok) throw new Error("Not logged in");
            return res.json();
        })
        .then(data => setUser(data.user))
        .catch(() => setUser(null))
        .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }

    const toggleSidebar = () => {
        setCollapsed((prev) => {
            localStorage.setItem("sidebarCollapsed", JSON.stringify(!prev));
        return !prev;
        });
    };

    console.log("App user:", user);
    return (
        // <Router>
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

                                    {/* 404 */}
                                    <Route path="*" element={<NotFound />} />
                                    </Route>
                                </Routes>
                            </div>
                        </Suspense>
                    
                </ToastProvider>
            </AuthProvider>
        </ErrorBoundary>
        // </Router>

        // <AuthContext.Provider value={{ user, setUser, loading }}>
        // <Routes>
            // Public Routes
        //     <Route path="/" element={<LandingPage /> } />
        //     <Route path="/login" element={<Login />} />
        //     <Route path="/register" element={<Register />} />

        //     Protected Routes
        //     <Route element={<ProtectedRoute />}>
        //         <Route element={<AppLayout collapsed={collapsed} toggleSidebar={toggleSidebar} />}>
        //             <Route path="/" element={<Dashboard />} />
        //             <Route path="dashboard" element={<Dashboard />} />
        //             <Route path="transactions" element={<Transactions />} />
        //             <Route path="budgets" element={<Budgets />} />
        //             <Route path="budget/:budget_id" element={<Budget />} />
        //             <Route path="subscriptions" element={<Subscriptions />} />
        //             <Route path="income" element={<Income />} />
        //             <Route path="friends" element={<Friends/>} />
        //             <Route path="shared-budgets" element={<SharedBudgets />} />
        //             <Route path="shared-budgets/:id" element={<SharedBudgetDetail />} />
        //         </Route>
        //     </Route>

        //     Catch-all
        //     <Route path="*" element={<LandingPage />} />
        // </Routes>
        // </AuthContext.Provider>
    );
}

export default App;