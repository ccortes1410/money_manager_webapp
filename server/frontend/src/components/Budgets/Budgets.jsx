import { useContext, useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import { useToast } from '../Toast/ToastContext';
import { apiFetch } from '../../utils/csrf';
import ExportButton from '../ExportButton/ExportButton';
import { EXPORT_CONFIGS } from '../../utils/export';
import './Budgets.css';
import '../Dashboard/Dashboard.css';
import Budget from './Budget';
import { Chart, ArcElement, Tooltip, Legend, Title } from 'chart.js';
import BudgetModal from './BudgetModal';
import BudgetCard from './BudgetCard';
import ConfirmDialog from '../ConfirmDialog/ConfirmDialog';

Chart.register(ArcElement, Tooltip, Legend, Title);

const Budgets = () => {
    const [budgets, setBudgets] = useState([]);
    const [selectedBudgetId, setSelectedBudgetId] = useState(null);
    const [budgetDetail, setBudgetDetail] = useState(null);
    const [budgetCache, setBudgetCache] = useState({});
    const [ loading, setLoading ] = useState(true);
    const [ showModal, setShowModal ] = useState(false);
    const [ editingBudget, setEditingBudget ] = useState(null);
    const [ filter, setFilter ] = useState("all");
    const { user } = useContext(AuthContext);
    const [ deleteConfirm, setDeleteConfirm ] = useState(null);

    const budgets_url = '/djangoapp/budgets';
    const navigate = useNavigate();
    const toast = useToast();

    const get_budgets = async () => {
        try {
            const response = await apiFetch(budgets_url, {
                method: 'GET',
            });

            const data = await response.json();

            if (data.budgets && Array.isArray(data.budgets)) {
                setBudgets(data.budgets);
            }
        } catch (error) {
            toast.error("Failed to load budgets");
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
            const response = await apiFetch(budget_url, {
                method: 'GET',
            });
            
            if (!response.ok) {
                throw new Error("Error fetching budget")
            }
            
            const data = await response.json();

            setBudgetDetail(data.budget);
            if (data.budget) {
                setBudgetCache(prev => ({
                    ...prev,
                    [budgetId]: data.budget
                }));
            }

            
        } catch (error) {
            console.log("Couldn't fetch budget:", error)
            toast.error("Failed to load budget details");
            setBudgetDetail(null);
        }
    }

    const handleCreate = async (budgetData) => {
        const add_url = `/djangoapp/budgets/create`;

        try {
            const response = await apiFetch(add_url, {
                method: 'POST',
                body: JSON.stringify(budgetData),
            });

            if (response.ok) {
                get_budgets();
                setShowModal(false);
                toast.success("Budget created succesfully");
            } else {
                toast.error("Failed to add budget");
            }
        } catch (error) {
            console.error("Error adding budget: ", error);
            toast.error("Something went wrong");
        }
    };

    const handleUpdate = async (budgetId, budgetData) => {
        const update_url = `/djangoapp/budgets/${budgetId}/update`;
        try {
            const response = await apiFetch(update_url, {
                method: 'PATCH',
                body: JSON.stringify(budgetData)
            });

            if (response.ok) {
                get_budgets();
                setShowModal(false);
                setEditingBudget(null);
                // Clear cache so detail refreshes
                setBudgetCache((prev) => {
                    const copy = { ...prev };
                    delete copy[budgetId];
                    return copy;
                });
                // Refresh deatil if it's selected
                if (selectedBudgetId === budgetId) {
                    get_budget(budgetId);
                }
                toast.success("Budget updated");
            } else {
                toast.error("Failed to update budget");
            }
        } catch (error) {
            console.error("Error updating budget:", error);
            toast.error("Something went wrong");
        }
    };

    const handleDelete = async (budgetId) => {
        if (!window.confirm("Delete this budget?")) return;

        const delete_url = `/djangoapp/budgets/${budgetId}/delete`;
        try {
            const response = await apiFetch(delete_url, {
                method: 'DELETE',
            });

            if (response.ok) {
                setBudgets((prev) => prev.filter((b) => b.i !== budgetId));
                if (selectedBudgetId === budgetId) {
                    setSelectedBudgetId(null);
                    setBudgetDetail(null);
                }
                // Clear from cache
                setBudgetCache((prev) => {
                    const copy = { ...prev };
                    delete copy[budgetId];
                    return copy;
                });
                toast.success("Budget deleted");
            } else {
                toast.error("Failed to delete budget");
            }
        } catch (error) {
            console.error("Error deleting budget:", error);
            toast.error("Something went wrong");
        } finally {
            setDeleteConfirm(null);
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
        const toggle_url = `/djangoapp/budgets/${budgetId}/toggle-recurring`;
        try {
            const response = await fetch(toggle_url, {
                method: 'PATCH',
                body: JSON.stringify({ 
                    is_recurring: isRecurring,
                    recurrence,
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
                toast.info(
                    isRecurring
                        ? `Budget set to recurring (${recurrence})`
                        : "Budget set to one-time"
                );
            } else {
                toast.error("Failed to update recurring status");
            }
        } catch (error) {
            console.error("Error toggling recurring status:", error);
            toast.error("Something went wrong");
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
    }, [user, navigate]);

    // Filter budgets
    const filteredBudgets = filter === "all"
        ? budgets
        : filter === "over"
            ? budgets.filter((b) => b.isOver)
            : filter === "on-track"
                ? budgets.filter((b) => !b.isOver && b.percentUsed >= 50)
                : budgets.filter((b) => b.percentUsed < 50);
    
    // Calculate totals
    const totals = useMemo(() => ({
        totalBudgeted: budgets.reduce((sum, b) => sum + Number(b.amount), 0),
        totalSpent: budgets.reduce((sum, b) => sum + b.spent, 0),
        overBudget: budgets.filter((b) => b.isOver).length,
        onTrack: budgets.filter((b) => !b.isOver).length,
    }), [budgets]);

    console.log("Budget detail:", budgetDetail);

    return (
            <div className="budgets-page">
                <div className="budgets-header">
                    <h1>Budgets</h1>
                    <div className="budgets-header-actions">
                        <ExportButton
                            data={filteredBudgets}
                            columns={EXPORT_CONFIGS.budgets.columns}
                            title={EXPORT_CONFIGS.budgets.getTile()}
                            subtitle={`${filteredBudgets.length} budgets - ${filter} filter`}
                            filename={EXPORT_CONFIGS.budgets.getFilename()}
                            summary={[
                                {
                                    label: "Total Budgeted",
                                    value: `$${totals.totalBudgeted.toFixed(2)}`,
                                    color: [59, 130, 246],
                                },
                                {
                                    label: "Total Spent",
                                    value: `$${totals.totalSpent.toFixed(2)}`,
                                    color: [239, 68, 68],
                                },
                                {
                                    label: "On Track",
                                    value: String(totals.onTrack),
                                    color: [34, 197, 94],
                                },
                                {
                                    label: "Over Budget",
                                    value: String(totals.overBudget),
                                    color: [245, 258, 11],
                                },
                            ]}
                            onExport={(status, message) => {
                                if (status === "success") toast.success(message);
                                else toast.error(message);
                            }}
                        />
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
                                    onDelete={() => setDeleteConfirm(budget.id)}
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

                {/* Delete Confirmaton */}
                {deleteConfirm && (
                    <ConfirmDialog
                        title="Delete Budget"
                        message="Are you sure you want to delete this budget? This action cannot be undone."
                        confirmText="Delete"
                        onConfirm={() => handleDelete(deleteConfirm)}
                        onCancel={() => setDeleteConfirm(null)}
                        danger
                    />
                )}
         </div>
    );
}

export default Budgets;
