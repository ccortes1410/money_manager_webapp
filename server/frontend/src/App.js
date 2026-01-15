import React, { useState, useEffect } from 'react';
import { AuthContext } from './AuthContext';
import Login from './components/Login/Login';
import { Routes, Route, Outlet } from 'react-router-dom';
import Register from './components/Register/Register';
import Dashboard from './components/Dashboard/Dashboard';
import Transactions from './components/Transactions/Transactions';
import Budget from './components/Budgets/Budget';
import Budgets from './components/Budgets/Budgets';
import AddBudget from './components/Budgets/AddBudget';
import Subscriptions from './components/Subscriptions/Subscriptions';
import Sidebar from './components/Sidebar/Sidebar';
import Income from './components/Income/Income';
import ProtectedRoute from './ProtectedRoute';
import "./App.css";
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
        <AuthContext.Provider value={{ user, setUser, loading }}>
        <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Routes */}
            <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout collapsed={collapsed} toggleSidebar={toggleSidebar} />}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="transactions" element={<Transactions />} />
                    <Route path="budgets" element={<Budgets />} />
                    <Route path="budget/:budget_id" element={<Budget />} />
                    <Route path="add-budget" element={<AddBudget />} />
                    <Route path="subscriptions" element={<Subscriptions />} />
                    <Route path="income" element={<Income />} />
                </Route>
            </Route>
        </Routes>
        </AuthContext.Provider>
    );
}

export default App;