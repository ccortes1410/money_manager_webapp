import React, { useState } from 'react';
import Login from './components/Login/Login';
import { Routes, Route, BrowserRouter } from 'react-router-dom';
import Register from './components/Register/Register';
import Dashboard from './components/Dashboard/Dashboard';
import Transactions from './components/Transactions/Transactions';
import Budget from './components/Budgets/Budget';
import Budgets from './components/Budgets/Budgets';
import AddBudget from './components/Budgets/AddBudget';
import Subscriptions from './components/Subscriptions/Subscriptions';
import Sidebar from './components/Sidebar/Sidebar';
import "./App.css";
// import Savings from './components/Savings/Savings';
// import Friends from './components/Friends/Friends';

function App() {
    const [ collapsed, setCollapsed ] = useState(
        () => JSON.parse(localStorage.getItem("sidebarCollapsed")) || false
    );

    const toggleSidebar = () => {
        setCollapsed((prev) => {
            localStorage.setItem("sidebarCollapsed", JSON.stringify(!prev));
        return !prev;
        });
    };

    return (
        <div className="app-layout">
            <Sidebar collapsed={collapsed} onToggle={toggleSidebar} />
            <main className={`main-content ${collapsed ? "collapsed" : ""}`}>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/transactions" element={<Transactions />} />
                    <Route path="/budgets" element={<Budgets />} />
                    <Route path="/budget/:budget_id" element={<Budget />} />
                    <Route path="/add-budget" element={<AddBudget />} />
                    <Route path="/subscriptions" element={<Subscriptions />} />
                    {/* <Route path="/savings" element={<Savings />} /> */}
                    {/* <Route path="/friends" element={<Friends />} /> */}
                </Routes>
            </main>
        </div>
    );
}

export default App;