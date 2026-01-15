import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import './Budgets.css';
import '../Dashboard/Dashboard.css';
import Sidebar from '../Sidebar/Sidebar';
import Budget from './Budget';
import { Pie } from 'react-chartjs-2';
import { Chart, ArcElement, Tooltip, Legend, Title } from 'chart.js';
import BudgetBar from './BudgetBar';

Chart.register(ArcElement, Tooltip, Legend, Title);

const Budgets = () => {
    const [budgets, setBudgets] = useState([]);
    // const [sharedBudgets, setSharedBudgets] = useState([]);
    const [transactions, setTransactions] = useState([]);
    const [selectedBudget, setSelectedBudget] = useState(null);
    const { user } = useContext(AuthContext);

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
                if (data.budgets.length > 0) {
                    setSelectedBudget(data.budgets[0].id);
                }
            }
        } catch (error) {
            alert('Error fetching budgets');
            setBudgets([]);
            console.error(error);
        }
    }

    const get_transactions = async () => {
        const transactions_url = `/djangoapp/transactions`;
        try {
            const response = await fetch(transactions_url, {
                method: 'GET',
                credentials: 'include'
            });
            const data = await response.json();
            setTransactions(data.transactions);
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

    const budgets_spent = budgets.map((b) => {
        const relatedTx = transactions.filter(
            (t) => t.category === b.category
        );

        const totalSpent = relatedTx.reduce((sum, t) => sum + Number(t.amount), 0);

        return { ...b, spent: totalSpent };
    })

    // console.log(myBudgets)

    const getPieChartData = (budget) => {
        if (!budget || !budget.amount || !Array.isArray(transactions)) {
            return {
                labels: [],
                datasets: []
            };
        }

        const txs = transactions.filter(tx => tx.category === budget.category);
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

    // const selectedBudget = budgets.find(b => b.id === selectedBudgetId);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/');
        }
    }, [user]); 


    return (
        // <div style={{ display: 'flex', width: '100vw', minHeight: '100vh' }}>
        //     <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
            <div className="budget-container">
                <div className="budget-header">
                    <h1 style={{ color: 'white', textAlign: 'center' }}>Budgets</h1>
                    <div className="active-user">
                        <p style={{ marginTop: '10px' }}>{user ? user.username : "Not Logged In"}</p>
                    </div>
                </div>
                
                <div className="budgets-view">
                    {/* My Budgets */}
                    <div className="budget-card">
                        <div className="budget-list header">
                            <h2>My Budgets</h2>
                            <button 
                                className="add-budget-button"
                                onClick={() => navigate('/add-budget')}
                            >
                                New Budget
                            </button>
                        </div>
                        <div className="budget-list">
                            {budgets_spent.map((b) => (
                                <BudgetBar
                                    key={b.id}
                                    budget={b}
                                    onSelect={() => setSelectedBudget(b)}
                                    onDelete={() => handleDeleteBudget(b.id)}
                                />                               
                            ))}
                        </div>
                    </div>

                    {/* Budget Details */}
                    <div className="budget-card">
                        <div className="budget-list header">
                            <h2>Budget Details</h2>
                        </div>
                        <div className="budget-info">
                        {selectedBudget ? (
                            <Budget 
                                budget={selectedBudget} 
                                transactions={transactions.filter(
                                    (t) => t.category === selectedBudget.category
                                )}
                            />
                        ) : (
                            <p>Select a budget to view details.</p>
                        )}
                        </div>
                    </div>

                    {/* Shared Budgets 
                    {/* <div className="budget-card">
                        <h2>Shared Budgets</h2>
                        {/* <div className='budget-list'>
                            {sharedBudgets.map((b) => (
                                <BudgetBar
                                    key={b.id}
                                    budget={b}
                                    shared
                                />
                            ))}
                        </div> *
                    </div> */}
                </div>
            </div>
        // </div>
    );
}

export default Budgets;
