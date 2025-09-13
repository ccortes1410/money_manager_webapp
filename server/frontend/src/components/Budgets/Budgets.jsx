import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Budgets.css';
import '../Dashboard/Dashboard.css';
import Sidebar from '../Sidebar/Sidebar';
import Budget from './Budget';
import { Pie } from 'react-chartjs-2';
import { Chart, ArcElement, Tooltip, Legend, Title } from 'chart.js';

Chart.register(ArcElement, Tooltip, Legend, Title);

const Budgets = () => {
    const [collapsed, setCollapsed] = useState(true);
    const [budgets, setBudgets] = useState([]);
    const [transactions, setTransactions] = useState([]);
    const [selectedBudgetId, setSelectedBudgetId] = useState(null);
    const [user, setUser] = useState(null);

    const budgets_url = '/djangoapp/budgets';
    const navigate = useNavigate();

    const get_budgets = async () => {
        try {
            const response = await fetch(budgets_url, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.budgets && Array.isArray(data.budgets)) {
                setBudgets(data.budgets);
                setUser(data.user);
                if (data.budgets.length > 0) {
                    setSelectedBudgetId(data.budgets[0].id);
                }
            }
        } catch (error) {
            alert('Error fetching budgets');
            setBudgets([]);
            setUser(null);
            console.error(error);
        }
    }

    const get_transactions = async () => {
        const transactions_url = `/djangoapp/dashboard`;
        try {
            const response = await fetch(transactions_url, {
                method: 'GET',
                credentials: 'include'
            });
            const data = await response.json();
            setTransactions(data.transactions || []);
        } catch (error) {
            alert('Error fetching transactions');
            setTransactions([]);
            console.error(error);
        }
    }

     const handleDeleteBudget = async (budgetId) => {
        const delete_url = `/djangoapp/budgets/${budgetId}/delete/`;
        try {
            const response = await fetch(delete_url, {
                method: 'DELETE',
                credentials: 'include',
                body: JSON.stringify({ id: budgetId }),
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) {
                throw new Error('Error deleting budget');
            }
            alert('Budget deleted successfully');
            window.location.href = '/budgets'; // Redirect to budgets page
        } catch (error) {
            alert('Error deleting budget: ' + error.message);
            console.error(error);
        }
    };

    useEffect(() => {
        get_budgets();
        get_transactions();
    }, []);

    useEffect(() => {
            if (user !== null && !user.is_authenticated) {
                navigate('/');
            }
    }, [user]);

    const getPieChartData = (budget) => {
        if (!budget || !budget.amount || !Array.isArray(transactions)) {
            return {
                labels: [],
                datasets: []
            };
        }

        const txs = transactions.filter(tx => tx.category === budget.name);
        const totalSpent = txs.reduce((sum, tx) => sum + Number(tx.amount), 0);
        const remaining = Math.max(Number(budget.amount) - totalSpent, 0);

        return {
            labels: ['Spent', 'Remaining'],
            datasets: [
                {
                    data: [totalSpent, remaining],
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                    ],
                    borderWidth: 1,
                }
                
            ]
        };
    }

    const pieChartOptions = {
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'top',
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let label = context.label || '';
                        let value = context.raw ?? 0;
                        return `${label}: $${Number(value)
                            .toLocaleString(undefined,
                            { 
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            })}`;
                    }
                }
            }
        }
    };

    const selectedBudget = budgets.find(b => b.id === selectedBudgetId);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/');
        }
    }, [user]); 

    return (
        <div style={{ display: 'flex', width: '100vw', minHeight: '100vh' }}>
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
            <div className="budget-container">
                <div className="budget-header">
                    <h1 style={{ color: 'white', textAlign: 'center' }}>My Budgets</h1>
                    <div className="active-user">
                        <p style={{ marginTop: '10px' }}>{user ? user.username : "Not Logged In"}</p>
                </div>
                </div>
                <button className="add-budget-button" onClick={() => navigate('/add-budget')}>Add Budget</button>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '32px', marginTop: '32px' }}>
                    {budgets.map(budget => {
                        const pieChartData = getPieChartData(budget);
                        return (
                            <div key={budget.id} style={{ minWidth: 200, textAlign: 'center' }}>
                                <h5>{budget.name}</h5>
                                {pieChartData.labels.length > 0 && pieChartData.datasets.length > 0 ? (
                                    <>
                                    <Pie 
                                        data={pieChartData}
                                        options={pieChartOptions}
                                        onClick={() => setSelectedBudgetId(budget.id)}
                                        style={{ cursor: 'pointer' }}
                                    />
                                    <button 
                                        className="delete-budget-button" 
                                        onClick={() => handleDeleteBudget(budget.id)}
                                    >
                                        Delete
                                    </button>
                                    </>
                                ) : (
                                    <p>No data available</p>
                                )}
                            </div>
                        )
                    })}
                </div>
                {selectedBudgetId && (
                    <div style={{ marginTop: '32px' }}>
                        <h3>Transactions for {selectedBudget.name}</h3>
                        <Budget selectedBudgetId={selectedBudgetId} />
                    </div>
                )}
                <p>Your total budget is: ${budgets.reduce((acc, item) => acc + Number(item.amount), 0)}</p>
            </div>
        </div>
    );
}

export default Budgets;
