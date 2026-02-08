import { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import './Budgets.css';
import '../Dashboard/Dashboard.css';
import Budget from './Budget';
import { Chart, ArcElement, Tooltip, Legend, Title } from 'chart.js';
import BudgetModal from './BudgetModal';
import BudgetCard from './BudgetCard';

Chart.register(ArcElement, Tooltip, Legend, Title);

const Budgets = () => {
    const [budgets, setBudgets] = useState([]);
    // const [sharedBudgets, setSharedBudgets] = useState([]);
    const [transactions, setTransactions] = useState([]);
    const [selectedBudgetId, setSelectedBudgetId] = useState(null);
    const [budgetDetail, setBudgetDetail] = useState(null);
    const [budgetCache, setBudgetCache] = useState({});
    const [ loading, setLoading ] = useState(true);
    const [ showModal, setShowModal ] = useState(false);
    const [ editingBudget, setEditingBudget ] = useState(null);
    const [ filter, setFilter ] = useState("all");
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
            }
        } catch (error) {
            alert('Error fetching budgets');
            setBudgets([]);
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

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
            if (data.budget) {
                setBudgetCache(prev => ({
                    ...prev,
                    [budgetId]: data.budget
                }));
            }

            
        } catch (error) {
            console.log("Couldn't fetch budget:", error)
            setBudgetDetail(null);
        }
    }

    // const get_transactions = async () => {
    //     const transactions_url = `/djangoapp/transactions`;
    //     try {
    //         const response = await fetch(transactions_url, {
    //             method: 'GET',
    //             credentials: 'include'
    //         });
    //         const data = await response.json();
    //         setTransactions(data.transactions || []);
    //     } catch (error) {
    //         console.error('Error fetching transactions', error);
    //         setTransactions([]);
    //     }
    // };

    const handleCreate = async (budgetData) => {
        const add_url = `/djangoapp/budgets/create`;

        try {
            const response = await fetch(add_url, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(budgetData),
            });

            if (response.ok) {
                get_budgets();
                setShowModal(false);
            } else {
                console.error("Failed to add budget");
            }
        } catch (error) {
            console.error("Error adding budget: ", error);
        }
    };

    const handleUpdate = async (budgetId, budgetData) => {
        const update_url = `/djangoapp/budgets/${budgetId}/update`;
        try {
            const response = await fetch(update_url, {
                method: 'PATCH',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(budgetData)
            });

            if (response.ok) {
                get_budgets();
                setShowModal(false);
                setEditingBudget(null);
            }
        } catch (error) {
            console.error("Error updating budget:", error);
        }
    };

    const handleDelete = async (budgetId) => {
        if (!window.confirm("Delete this budget?")) return;

        const delete_url = `/djangoapp/budgets/${budgetId}/delete`;
        try {
            const response = await fetch(delete_url, {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                setBudgets((prev) => prev.filter((b) => b.i !== budgetId));
                if (selectedBudgetId === budgetId) {
                    setSelectedBudgetId(null);
                    setBudgetDetail(null);
                }
            }
        } catch (error) {
            console.error("Error deleting budget:", error);
        }
    };

    const handleEdit = (budget) => {
        setEditingBudget(budget);
        setShowModal(true);
    };

    const handleSelectBudget = (budgetId) => {
        setSelectedBudgetId(prev => prev === budgetId ? null : budgetId);
    };

    const handleToggleRecurring = async (budgetId, isRecurring, recurrence = "monthly") => {
        try {
            const response = await fetch(`/djangoapp/budgets/${budgetId}/toggle-recurring`, {
                method: 'PATCH',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    is_recurring: isRecurring,
                    recurrence 
                })
            });
            
            if (response.ok) {
                setBudgets((prev) => 
                    prev.map((b) =>
                        b.id === budgetId
                            ? { ...b, is_recurring: isRecurring, recurrence}
                            : b
                    )
                );
            }
        } catch (error) {
            console.error("Error toggling recurring status:", error);
        }
    };

    useEffect(() => {
        get_budgets();
    }, [])

    useEffect(() => {
        if (selectedBudgetId === null) return;
        get_budget(selectedBudgetId);
    }, [selectedBudgetId]);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/');
        }
    }, [user]);

    // Calculate spent amount for each budget
    // const budgetsWithSpent = budgets.map((b) => {
    //     const relatedTx = transactions.filter((t) => t.category === b.category);
    //     const totalSpent = relatedTx.reduce((sum, t) => sum + Number(t.amount), 0);
    //     const percentUsed = b.amount > 0 ? (totalSpent / b.amount) *100 : 0;
    //     const isOver = totalSpent > b.amount;
    //     return { ...b, spent: totalSpent, percentUsed, isOver };
    // });

    // Filter budgets
    const filteredBudgets = filter === "all"
        ? budgets
        : filter === "over"
            ? budgets.filter((b) => b.isOver)
            : filter === "on-track"
                ? budgets.filter((b) => !b.isOver && b.percentUsed >= 50)
                : budgets.filter((b) => b.percentUsed < 50);
    
    // Calculate totals
    const totals = {
        totalBudgeted: budgets.reduce((sum, b) => sum + Number(b.amount), 0),
        totalSpent: budgets.reduce((sum, b) => sum + b.spent, 0),
        overBudget: budgets.filter((b) => b.isOver).length,
        onTrack: budgets.filter((b) => !b.isOver).length,
    };

    console.log("Budget detail:", budgetDetail);
    console.log("Filtered Budgets:", filteredBudgets)
    return (
            <div className="budgets-page">
                <div className="budgets-header">
                    <h1>Budgets</h1>
                    <button
                        className='budgets-add-btn'
                        onClick={() => {
                            setEditingBudget(null);
                            setShowModal(true);
                        }}
                    >
                        + Add Budget
                    </button>
                </div>
                
                {/* Summary Cards */}
                <div className="budgets-summary">
                    <div className="bd-summary-card total">
                        <span className="label">Total Budgeted</span>
                        <span className="value">${totals.totalBudgeted.toFixed(2)}</span>
                    </div>
                    <div className="bd-summary-card spent">
                        <span className="label">Total Spent</span>
                        <span className="value">${totals.totalSpent.toFixed(2)}</span>
                    </div>
                    <div className="bd-summary-card on-track">
                        <span className="label">On Track</span>
                        <span className="value">{totals.onTrack}</span>
                    </div>
                    <div className="bd-summary-card over">
                        <span className="label">Over Budget</span>
                        <span className="value">{totals.overBudget}</span>
                    </div>
                </div>

                {/* Filter tabs */}
                <div className="filter-tabs">
                    {[
                        { key: "all", label: "All" },
                        { key: "on-track", label: "On Track" },
                        { key: "under", label: "Under 50%" },
                        { key: "over", label: "Over Budget" }
                    ].map(({ key, label }) => (
                        <button
                            key={key}
                            className={`filter-tab ${filter === key ? "active" : ""}`}
                            onClick={() => setFilter(key)}
                        >
                            {label}
                            <span className="count">
                                {key === "all"
                                    ? budgets.length
                                    : key === "over"
                                        ? budgets.filter((b) => b.isOver).length
                                        :key === "on-track"
                                            ? budgets.filter((b) => !b.isOver && b.percentUsed >= 50).length
                                            : budgets.filter((b) => b.percentUsed < 50).length}
                            </span>
                        </button>
                    ))}
                </div>
                
                {/* Main Content */}
                <div className="budgets-content">
                    {/* Budgets List */}
                    <div className="budgets-list">
                        {loading ? (
                            <p className="loading-state">Loading budgets...</p>
                        ) : filteredBudgets.length === 0 ? (
                            <p className="empty-state">No budgets found.</p>
                        ) : (
                            filteredBudgets.map((budget) => (
                                <BudgetCard
                                    key={budget.id}
                                    budget={budget}
                                    isSelected={selectedBudgetId === budget.id}
                                    onSelect={() => handleSelectBudget(budget.id)}
                                    onEdit={() => handleEdit(budget)}
                                    onDelete={() => handleDelete(budget.id)}
                                    onToggleRecurring={(isRecurring) => 
                                        handleToggleRecurring(budget.id, isRecurring, budget.recurrence || "monthly")
                                    }
                                />
                            ))
                        )}
                    </div>

                    {/* Budget Details Panel */}
                    <div className="budget-details-panel">
                        <h2>Budget Details</h2>
                        {selectedBudgetId ? (
                            budgetDetail ? (
                                <Budget
                                    budget={budgetDetail}
                                />
                            ) : (
                                <p className="loading-state">Loading details...</p>
                            ) 
                        ) : (
                            <p className="empty-state">Select a budget to view details.</p>
                        )}
                    </div>
                </div>

                {/* Modal */}
                {showModal && (
                    <BudgetModal
                        budget={editingBudget}
                        onClose={() => {
                            setShowModal(false);
                            setEditingBudget(null);
                        }}
                        onSave={(data) => {
                            if (editingBudget) {
                                handleUpdate(editingBudget.id, data);
                            } else {
                                handleCreate(data);
                            }
                        }}
                    />
                )}
         </div>
    );
}

export default Budgets;
