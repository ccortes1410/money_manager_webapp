import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import './Budgets.css';
import '../Dashboard/Dashboard.css';
import Budget from './Budget';
// import { Pie } from 'react-chartjs-2';
import { Chart, ArcElement, Tooltip, Legend, Title } from 'chart.js';
import BudgetBar from './BudgetBar';

Chart.register(ArcElement, Tooltip, Legend, Title);

const Budgets = () => {
    const [budgets, setBudgets] = useState([]);
    // const [sharedBudgets, setSharedBudgets] = useState([]);
    const [transactions, setTransactions] = useState([]);
    const [selectedBudgetId, setSelectedBudgetId] = useState(null);
    const [budgetDetail, setBudgetDetail] = useState(null);
    const [budgetCache, setBudgetCache] = useState({});
    const { user } = useContext(AuthContext);

    const [ categoryInput, setCategoryInput ] = useState("");
    const [ amountInput, setAmountInput ] = useState("");
    const [ periodStart, setPeriodStart ] = useState("");
    const [ periodEnd, setPeriodEnd ] = useState("");
    const [ recurrenceInput, setRecurrence ] = useState("");
    // const [ isShared, setIsShared ] = useState(null);

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
                // if (data.budgets.length > 0) {
                //     setSelectedBudget(data.budgets[0].id);
                // }
            }
        } catch (error) {
            alert('Error fetching budgets');
            setBudgets([]);
            console.error(error);
        }
    }

    const get_budget = async (budgetId) => {
        if (budgetCache[budgetId]) {
            setBudgetDetail(budgetCache[budgetId]);
            return;
        }

        const budget_url = `/djangoapp/budget/${budgetId}`;
        try {
            const response = await fetch(budget_url, {
                method: 'GET',
                credentials:'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json()

            if (!response.ok) {
                throw new Error("Error fetching budget")
            }
            
            setBudgetDetail(data.budget);
            if (Array.isArray(data.budget)) {
                setBudgetCache(prev => ({
                    ...prev,
                    [budgetId]: data.budget
                }));
            }

            
        } catch (error) {
            console.log("Couldn't fetch budget:", error)
            setBudgetDetail([])
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

    const handleAddBudget = async () => {
        const add_url = `/djangoapp/budgets/add`;

        const amount = amountInput;
        const category = categoryInput;
        const period_start = periodStart;
        const period_end = periodEnd;
        const recurrence = recurrenceInput;

        const newBudget = {
            amount: parseFloat(amount),
            category: category,
            period_start: period_start,
            period_end: period_end,
            recurrence: recurrence
        }

        try {
            const response = await fetch(add_url, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type' : 'application/json'
                },
                body: JSON.stringify(newBudget),
            });

            const res = await response.json();
            
            if (response.ok) {
                get_budgets();
                setAmountInput("");
                setCategoryInput("");
                setPeriodStart("");
                setPeriodEnd("");
                setRecurrence("");
            } else {
                console.error("Failed to add budget");
            }
        } catch (error) {
            console.error("Error adding budget: ", error);
        }
    }

    const handleStopBudget = async (budgetId) => {
        const update_url = `/djangoapp/budgets/${budgetId}/update`;
        try {
            const response = await fetch(update_url, {
                method: 'PATCH',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: { is_recurring: false}
            });

            if (!response.ok) {
                throw new Error('Error updating budget');
            }
        } catch (error) {
            alert('Error updating budget: ' + error.message);
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
        if (selectedBudgetId === null) return;
        get_budget(selectedBudgetId);
    }, [selectedBudgetId]);

    const budgets_spent = budgets.map((b) => {
        const relatedTx = transactions.filter(
            (t) => t.category === b.category
        );

        const totalSpent = relatedTx.reduce((sum, t) => sum + Number(t.amount), 0);

        return { ...b, spent: totalSpent };
    })

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/');
        }
    }, [user]); 

    console.log("Selected Budget:", selectedBudgetId)
    console.log("Budget detail:", budgetDetail)

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
                <div className="bud-input-header">
                <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
                        <input
                            id='amount-input'
                            className='bud-text-input'
                            type="number"
                            placeholder='Amount'
                            value={amountInput}
                            onChange={(e) => setAmountInput(e.target.value)}
                        />
                        <input
                            id='category-input'
                            className='bud-text-input'
                            type="text"
                            placeholder='Category'
                            value={categoryInput}
                            onChange={(e) => setCategoryInput(e.target.value)}
                        />
                        <input 
                            id="start-date-input"
                            type="date"
                            className="bud-date-input"
                            value={periodStart}
                            onChange={(e) => setPeriodStart(e.target.value)}
                        />
                        <input
                            id="end-date-input"
                            type="date"
                            className="bud-date-input"
                            value={periodEnd}
                            onChange={(e) => setPeriodEnd(e.target.value)}
                        />
                        <select
                            id='recurrence-input'
                            className='bud-rec-input'
                            type="date"
                            value={recurrenceInput}
                            onChange={(e) => setRecurrence(e.target.value)}
                            >
                                <option value="">Select Recurrence</option>
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                                <option value="yearly">Yearly</option>
                        </select>
                        <button
                            className="add-btn"
                            onClick={handleAddBudget}
                        >
                            +
                        </button>
                        <button
                            className="stop-btn"
                            onClick={() => handleStopBudget(selectedBudgetId)}
                            style={{ marginLeft: '10px' }}
                        >
                            Stop
                        </button>
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
                            {budgets.map((b) => (
                                <BudgetBar
                                    key={b.id}
                                    budget={b}
                                    onSelect={() => setSelectedBudgetId(b.id)}
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
                        {selectedBudgetId ? (
                            <Budget 
                                budget={budgetDetail} 
                                // transactions={budgetDetail.transactions}
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
