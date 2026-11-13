import React, { useState, useEffect, useCallback } from 'react';
import './Dashboard.css';
import '../assets/style.css';
import { BarElement, ArcElement, Chart, LineController, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Title } from 'chart.js';
import PeriodSelector from './PeriodSelector';
import TransactionsCard from './Dashboard Cards/TransactionsCard';
import CategorySpendingCard from './Dashboard Cards/CategorySpendingCard';
import SubscriptionsCard from './Dashboard Cards/SubscriptionsCard';
import BudgetsCard from './Dashboard Cards/BudgetsCard';
import IncomeCard from './Dashboard Cards/IncomeCard';
import { apiFetch } from '../../utils/csrf';

Chart.register(BarElement, ArcElement, LineController, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Title);

const PERIODS = ["daily", "weekly", "monthly", "yearly", "total"];

const Dashboard = () => {
    const [ dashboard, setDashboard ] = useState({
        transactions: [],
        categories: {
            categories: [],
            total: 0,
            transaction_total: 0,
            subscription_total: 0,
        },
        subscriptions: {
            active_count: 0,
            paused_count: 0,
            monthly_cost: 0,
            upcoming: [],
        },
        budgets: {
            total_budgeted: 0,
            total_spent: 0,
            remaining: 0,
            percent_used: 0,
        },
        income: {
            total_income: 0,
            total_spent: 0,
            remaining: 0,
        },
        period: {
            value: "monthly",
            label: "Last 30 Days",
        },
    });
    const [ error, setError ] = useState(null);
    const [ loading, setLoading ] = useState(true);
    const [ selectedPeriod, setSelectedPeriod ] = useState("monthly");

    const dashboard_url = "/djangoapp/dashboard";

    const get_dashboard = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const res = await apiFetch(`${dashboard_url}?period=${selectedPeriod}`, {
                method: 'GET',
            });
            
            if (!res.ok) throw new Error("Failed to fetch dashboard");

            const data = await res.json();
            setDashboard(data.dashboard);
        } catch (err) {
            console.error("Couldn't fetch dashboard:", err);
            setError("Failed to load dashboard data");
        } finally {
            setLoading(false);
        }
    }, [selectedPeriod]);

    useEffect(() => {
        get_dashboard();
    }, [get_dashboard]);

    if (error) {
        return (
            <div className="dashboard-error">
                <p>{error}</p>
                <button onClick={get_dashboard}>
                    Retry
                </button>
            </div>
        );
    }
    
    if (loading) {
        return (
            <div className="dashboard-page">
                <div className="dashboard-header">
                    <h1>Dashboard</h1>
                </div>
                <div className="period-selector-wrapper">
                    <PeriodSelector
                        periods={PERIODS}
                        selected={selectedPeriod}
                        onSelect={setSelectedPeriod}
                    />
                </div>
                <div className="dashboard-loading">
                    <p>Loading dashboard...</p>
                </div>
            </div>
        );
    }

    return (  
        <div className="dashboard-page">
            {/* Fixed header */}
            <div className="dashboard-header">
                <h1>Dashboard</h1>
            </div>

            {/* Fixed period selector */}
            <div className="period-selector-wrapper">
                <PeriodSelector
                    periods={PERIODS}
                    selected={selectedPeriod}
                    onSelect={setSelectedPeriod}
                />
            </div>

            {/* Scrollable content */}
            <div className="dashboard-content">
                {/* Main cards grid */}
                <div className="dashboard-main">
                    <div className="dashboard-card transactions">
                        <TransactionsCard
                            transactions={dashboard?.transactions || []}
                            period={selectedPeriod}
                        />
                    </div>

                    <div className="dashboard-card categories">
                        <CategorySpendingCard
                            key={dashboard?.categories?.total}
                            categories={dashboard?.categories || {}}
                            period={selectedPeriod}
                        />
                    </div>

                    <div className="dashboard-card subscriptions">
                        <SubscriptionsCard
                            subscriptions={dashboard?.subscriptions}
                            period={selectedPeriod}
                        />
                    </div>

                    <div className="dashboard-card budgets">
                        <BudgetsCard
                            budgets={dashboard?.budgets}
                            period={selectedPeriod}
                        />
                    </div>
                </div>

                {/* Income sidebar */}
                <div className="dashboard-sidebar">
                    <div className="dashboard-card income">
                        <IncomeCard
                            income={dashboard?.income}
                            period={selectedPeriod}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;