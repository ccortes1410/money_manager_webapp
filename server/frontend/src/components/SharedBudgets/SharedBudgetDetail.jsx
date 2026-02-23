import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import AddExpenseModal from './AddExpenseModal';
import SettleUpModal from './SettleUpModal';
import InviteFriendModal from './InviteFriendModal';
import './SharedBudgets.css';

const SharedBudgetDetail = () => {
    const [ budget, setBudget ] = useState(null);
    const [ loading, setLoading ] = useState(true);
    const [ showExpenseModal, setShowExpenseModal ] = useState(false);
    const [ showSettleModal, setShowSettleModal ] = useState(false);
    const [ showInviteModal, setShowInviteModal ] = useState(false);
    const [ activeSection, setActiveSection ] = useState("expenses");

    const { id } = useParams();
    const { user } = useContext(AuthContext);
    const navigate = useNavigate();
    const baseUrl = "/djangoapp";

    const fetchBudgetDetail = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${baseUrl}/shared-budgets/${id}`, {
                credentials: 'include',
            });
            const data = await res.json();

            if (res.ok) {
                setBudget(data);
            } else {
                alert(data.error || "Failed to load budget");
                navigate("/shared-budgets");
            }
        } catch (error) {
            console.error("Error fetching budget detail:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddExpense = async (expenseData) => {
        try {
            const res = await fetch(`${baseUrl}/shared-budgets/${id}/expenses/add`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(expenseData),
            });
            const data = await res.json();

            if (res.ok) {
                fetchBudgetDetail();
                setShowExpenseModal(false);
            } else {
                alert(data.error || "Failed to add expense");
            }
        } catch (error) {
            console.error("Error adding expense:", error);
        }
    };

    const handleDeleteExpense = async (expenseId) => {
        if (!window.confirm("Delete this expense?")) return;

        try {
            const res = await fetch(`${baseUrl}/shared-budgets/${id}/expenses/${expenseId}/delete`, {
                method: 'DELETE',
                credentials: 'include'
            });
            const data = await res.json();

            if (res.ok) {
                fetchBudgetDetail();
            } else {
                alert(data.error || "Failed to delete expense");
            }
        } catch (error) {
            console.error("Error deleting expense:", error);
        }
    };

    const handleSettle = async (settlementData) => {
        try {
            const res = await fetch(`${baseUrl}/shared-budgets/${id}/settle`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settlementData),
            });
            const data = await res.json();

            if (res.ok) {
                fetchBudgetDetail();
                setShowSettleModal(false);
            } else {
                alert(data.error || "Failed to record settlement");
            }
        } catch (error) {
            console.error("Error recording settlement:", error);
        }
    };

    const handleLeaveBudget = async () => {
        if (!window.confirm("Are you sure you want to leave this budget?")) return;

        try {
            const res = await fetch(`${baseUrl}/shared-budgets/${id}/leave`, {
                method: 'POST',
                credentials: 'include',
            });
            const data = await res.json();

            if (res.ok) {
                navigate("/shared-budgets");
            } else {
                alert(data.error || "Failed to leave budget");
            }
        } catch (error) {
            console.error("Error leaving budget:", error);
        }
    };

    const getAvatarColor = (username) => {
        const colors = [
            "#3b82f6",
            "#22c55e",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
            "#ec4899",
            "#06b6d4",
            "#f97316"
        ]
        if (!username) return colors[0];
        return colors[username.charAt(0) % colors.length];
    };

    const getInitials = (userObj) => {
        if (userObj.first_name && userObj.last_name) {
            return `${userObj.first_name[0]}${userObj.last_name[0]}`.toUpperCase();
        }
        return userObj.username?.slice(0, 2).toUpperCase() || "??";
    };

    const formatCurrency = (value) => parseFloat(value || 0).toFixed(2);

    const formatDate = (dateString) => {
        if (!dateString) return "";
        return new Date(dateString).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    };

    const getProgressColor = (progress) => {
        if (progress >= 90) return "#ef4444";
        if (progress >= 70) return "#f59e0b";
        return "#22c55e";
    };

    useEffect(() => {
        fetchBudgetDetail();
    }, [id]);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate("/login");
        }
    }, [user, navigate]);

    if (loading) {
        return (
            <div className="shared-budgets-page">
                <div className="sb-loading">Loading budget details...</div>
            </div>
        );
    }

    if (!budget) {
        return (
            <div className="shared-budgets-page">
                <div className="sb-empty">Budget not found</div>
            </div>
        );
    }

    const canEdit = budget.user_role === "owner" || budget.user_role === "editor";
    const isOwner = budget.user_role === "owner";
    const expenses = Array.isArray(budget.expenses) ? budget.expenses : [];
    const debts = Array.isArray(budget.debts) ? budget.debts : [];
    const settlements = Array.isArray(budget.settlements) ? budget.settlements : [];
    const members = Array.isArray(budget.members) ? budget.members : [];

    return (
        <div className="shared-budgets-page">
            {/* Back Button & Header */}
            <div className="sbd-header">
                <button 
                    className="sbd-back-btn" 
                    onClick={() => navigate("/shared-budgets")}
                >
                   ← Back     
                </button>
                <div className="sbd-header-info">
                    <h1>{budget.name}</h1>
                    {budget.category && (
                        <span className="sb-category-badge">{budget.category}</span>
                    )}
                    <span className="sb-role-badge">{budget.user_role}</span>
                </div>
                <div className="sbd-header-actions">
                    {canEdit && (
                        <>
                            <button
                                className="sbd-action-btn primary"
                                onClick={() => setShowInviteModal(true)}
                            >
                                + Add Expense
                            </button>
                            <button
                                className="sbd-action-btn secondary"
                                onClick={() => setShowInviteModal(true)}
                            >
                                👥 Invite
                            </button>
                        </>
                    )}
                    {debts.length > 0 && (
                        <button
                            className="sbd-action-btn settle"
                            onClick={()=> setShowSettleModal(true)}
                        >
                            💰 Settle Up
                        </button>
                    )}
                </div>
            </div>

            {/* Summary Cards */}
            <div className="sbd-primary">
                <div className="sbd-summary-card">
                    <span className="sbd-summary-label">Total Budget</span>
                    <span className="sbd-summary-value">
                        ${formatCurrency(budget.total_amount)}
                    </span>
                </div>
                <div className="sbd-summary-card">
                    <span className="sbd-summary-label">Total Spent</span>
                    <span className="sbd-summary-value">
                        ${formatCurrency(budget.total_spent)}
                    </span>
                </div>
                <div className="sbd-summary-card">
                    <span className="sbd-summary-label">Remaining</span>
                    <span className={`sbd-summary-value ${budget.remaining < 0 ? "negative" : "positive"}`}>
                        ${formatCurrency(budget.remaining)}
                    </span>
                </div>
                <div className="sbd-summary-card">
                    <span className="sbd-summary-label">Your Balance</span>
                    <span
                        className={`sbd-summary-value ${
                            budget.user_balance > 0
                                ? "positive"
                                : budget.user_balance < 0
                                ? "negative"
                                : "neutral"
                        }`}
                    >
                        {budget.user_balance > 0
                            ? `+ $${formatCurrency(budget.user_balance)}`
                            : budget.user_balance < 0
                            ? `- $${formatCurrency(Math.abs(budget.user_balance))}`
                            : "\$0.00 ✓"}
                    </span>
                </div>
            </div>

            {/* Progress Bar */}
            <div className="sbd-progress">
                <div className="sbd-progress-bar">
                    <div
                        className="sbd-progress-fill"
                        style={{
                            width: `${Math.min(budget.progress, 100)}%`,
                            backgroundColor: getProgressColor(budget.progress),
                        }}
                    />
                </div>
                <span className="sbd-progress-text">{budget.progress}% spent</span>
            </div>

            {/* Main Content */}
            <div className="sbd-content">
                {/* Left Panel */}
                <div className="sbd-left-panel">
                    {/* Section Tabs */}
                    <div className="sbd-section-tabs">
                        <button
                            className={`sbd-section-tab ${activeSection === "expenses" ? "active" : ""}`}
                            onClick={() => setActiveSection("expenses")}
                        >
                            Expenses ({expenses.length})
                        </button>
                        <button
                            className={`sbd-section-tab ${activeSection === "debts" ? "active" : ""}`}
                            onClick={() => setActiveSection("debts")}
                        >
                            Debts {debts.length > 0 && `(${debts.legnth})`}
                        </button>
                        <button
                            className={`sbd-section-tab ${activeSection === "settlements" ? "active" : ""}`}
                            onClick={() => setActiveSection("settlements")}
                        >
                            Settlements ({settlements.length})
                        </button>
                    </div>

                    {/* Expenses List */}
                    {activeSection === "expenses" && (
                        <div className="sbd-length-list">
                            {expenses.length === 0 ? (
                                <div className="sbd-section-empty">
                                    <p>No expenses yet</p>
                                    {canEdit && (
                                        <button
                                            className="sbd-action-btn primary small"
                                            onClick={() => setShowExpenseModal(true)}
                                        >
                                            + Add First Expense
                                        </button>
                                    )}
                                </div>
                            ) : (
                                expenses.map((expense) => (
                                    <div key={expense.id} className="sbd-expense-item">
                                        <div className="sbd-expense-main">
                                            <div
                                                className="sbd-expense-avatar"
                                                style={{
                                                    backgroundColor: getAvatarColor(expense.paid_by.username),
                                                }}
                                            >
                                                {expense.paid_by.username?.slice(0, 1).toUpperCase()}
                                            </div>
                                            <div className="sbd-expense-info">
                                                <h4>{expense.description}</h4>
                                                <p>
                                                    Paid by{" "}
                                                    <strong>{expense.paid_by.username}</strong>
                                                    {expense.category && ` • ${expense.category}`}
                                                </p>
                                                <span className="sbd-expense-date">
                                                    {formatDate(expense.date)}
                                                </span>
                                            </div>
                                            <div className="sbd-expense-right">
                                                <span className="sbd-expense-amount">
                                                    ${formatCurrency(expense.amount)}
                                                </span>
                                                {canEdit && (
                                                    <button
                                                        className="sbd-delete-btn"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDeleteExpense(expense.id);
                                                        }}
                                                    >
                                                        🗑️
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                        {/* Splits */}
                                        <div className="sbd-expense-splits">
                                            {expense.splits.map((split) => (
                                                <span key={split.id} className="sbd-split-item">
                                                    {split.user.username}: ${formatCurrency(split.amount_owed)}
                                                    {split.is_settled && " ✓"}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {/* Debts List */}
                    {activeSection === "debts" && (
                        <div className="sbd-debts-list">
                            {debts.length === 0 ? (
                                <div className="sbd-section-empty">
                                    <span className="sbd-settled-icon">✅</span>
                                    <p>All settled up!</p>
                                </div>
                            ) : (
                                debts.map((debt, index) => (
                                    <div key={index} className="sbd-debt-item">
                                        <div
                                            className="sbd-debt-avatar"
                                            style={{
                                                backgroundColor: getAvatarColor(debt.from_user.username),
                                            }}
                                        >
                                            {debt.from_user.username?.slice(0, 1).toUpperCase()}
                                        </div>
                                        <div className="sbd-debt-info">
                                            <span className="sbd-debt-from">
                                                {debt.from_user.username}
                                            </span>
                                            <span className="sbd-debt-arrow">→</span>
                                            <span className="sbd-debt-to">
                                                {debt.to_user.username}
                                            </span>
                                        </div>
                                        <span className="sbd-debt-amount">
                                            ${formatCurrency(debt.amount)}
                                        </span>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {/* Settlements List */}
                    {activeSection === "settlements" && (
                        <div className="sbd-settlements-list">
                            {settlements.length === 0 ? (
                                <div className="sbd-section-empty">
                                    <p>No settlements recorded yet</p>
                                </div>
                            ) : (
                                settlements.map((settlement) => (
                                    <div key={settlement.id} className="sbd-settlement-item">
                                        <div className="sbd-settlement-info">
                                            <span className="sbd-settlement-payer">
                                                {settlement.payer.username}
                                            </span>
                                            <span className="sbd-settlement-arrow">
                                                paid →
                                            </span>
                                            <span className="sbd-settlement-receiver">
                                                {settlement.receiver.username}
                                            </span>
                                        </div>
                                        <div className="sbd-settlement-right">
                                            <span className="sbd-settlement-amount">
                                                ${formatCurrency(settlement.amount)}
                                            </span>
                                            <span className="sbd-settlement-date">
                                                {formatDate(settlement.date)}
                                            </span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>

                {/* Right Panel: Members */}
                <div className="sbd-right-panel">
                    <div className="sbd-members-section">
                        <h3>Members ({members.length})</h3>
                        <div className="sbd-members-list">
                            {members.map((member) => (
                                <div key={member.id} className="sbd-member-item">
                                    <div
                                        className="sbd-member-avatar-lg"
                                        style={{
                                            backgroundColor: getAvatarColor(member.user.username),
                                        }}
                                    >
                                        {getInitials(member.user)}
                                    </div>
                                    <div className="sbd-member-info">
                                        <span className="sbd-member-name">
                                            {member.user.first_name || member.user.username}
                                            {member.user.id === user?.id && " (You)"}
                                        </span>
                                        <span className="sb-role-badge small">
                                            {member.role}
                                        </span>
                                    </div>
                                    <div className="sbd-member-stats">
                                        <span className="sbd-member-paid">
                                            Paid: ${formatCurrency(member.total_paid)}
                                        </span>
                                        <span
                                            className={`sbd-member-balance ${
                                                member.balance > 0
                                                    ? "positive"
                                                    : member.balance < 0
                                                    ? "negative"
                                                    : ""
                                            }`}
                                        >
                                            {member.balance > 0
                                                ? `+ $${formatCurrency(member.balance)}`
                                                : member.balance < 0
                                                ?   `- $${formatCurrency(Math.abs(member.balance))}`
                                                : "Settled"}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Budget Info */}
                    <div className="sbd-info-section">
                        <h3>Budget Info</h3>
                        <div className="sbd-info-list">
                            <div className="sbd-info-item">
                                <span className="sbd-info-label">Period</span>
                                <span className="sbd-info-value">
                                    {formatDate(budget.start_date)} - {formatDate(budget.end_date)}
                                </span>
                            </div>
                            <div className="sbd-info-item">
                                <span className="sbd-info-label">Split Type</span>
                                <span className="sbd-info-value">{budget.default_split_type}</span>
                            </div>
                            <div className="sbd-info-item">
                                <span className="sbd-info-label">Created By</span>
                                <span className="sbd-info-value">{budget.created_by.username}</span>
                            </div>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="sbd-panel-actions">
                        {!isOwner && (
                            <button className="sbd-leave-btn" onClick={{handleLeaveBudget}}>
                                Leave Budget
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Modals */}
            {showExpenseModal && (
                <AddExpenseModal
                    members={members}
                    splitType={budget.default_split_type}
                    onClose={() => setShowExpenseModal(false)}
                    onSave={handleAddExpense}
                />
            )}

            {showSettleModal && (
                <SettleUpModal
                    debts={debts}
                    userId={user?.id}
                    onClose={() => setShowSettleModal(false)}
                    onSave={handleSettle}
                />
            )}

            {showInviteModal && (
                <InviteFriendModal
                    budgetId={budget.id}
                    existingMembers={members.map((m) => m.user.id)}
                    onClose={() => setShowInviteModal(false)}
                    onInvited={() => fetchBudgetDetail()}
                />
            )}
        </div>
    );
};

export default SharedBudgetDetail;