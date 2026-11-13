import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../../utils/csrf';
import { getAvatarColor, getInitials } from '../../utils/formatters';
import CreateSharedBudgetModal from './CreateSharedBudgetModal';
import './SharedBudgets.css';


const SharedBudgets = () => {
    const [ activeBudgets, setActiveBudgets ] = useState([]);
    const [ inactiveBudgets, setInactiveBudgets ] = useState([]);
    const [ pendingInvites, setPendingInvites ] = useState([]);
    const [ loading, setLoading ] = useState(true);
    const [ showCreateModal, setShowCreateModal ] = useState(false);
    const [ activeTab, setActiveTab ] = useState('active');

    const navigate = useNavigate();
    const baseUrl = "/djangoapp";

    const fetchBudgets = async () => {
        setLoading(true);
        try {
            const res = await apiFetch(`${baseUrl}/shared-budgets`);

            const data = await res.json();

            if (res.ok) {
                setActiveBudgets(Array.isArray(data.active_budgets) ? data.active_budgets : []);
                setInactiveBudgets(Array.isArray(data.inactive_budgets) ? data.inactive_budgets : []);
                setPendingInvites(Array.isArray(data.pending_invites) ? data.pending_invites : []);
            }
        } catch (error) {
            console.error("Error fetching shared budgets:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateBudget = async (budgetData) => {
        try {
            const res = await apiFetch(`${baseUrl}/shared-budgets/create`, {
                method: 'POST',
                body: JSON.stringify(budgetData),
            });
            const data = await res.json();

            if (res.ok) {
                fetchBudgets();
                setShowCreateModal(false);
            } else {
                alert(data.error || "Failed to create budget");
            }
        } catch (error) {
            console.error("Error creating budget:", error);
        }
    };

    const handleRespondToInvite = async (inviteId, action) => {
        try {
            const res = await apiFetch(`${baseUrl}/shared-budgets/invite/${inviteId}/respond`, {
                method: 'POST',
                body: JSON.stringify({ action }),
            });
            const data = await res.json();

            if (res.ok) {
                fetchBudgets();
            } else {
                alert(data.error || "Failed to respond to invite");
            }
        } catch (error) {
            console.error("Error responding to invite:", error);
        }
    };

    const formatCurrency = (value) => {
        return parseFloat(value || 0).toFixed(2);
    };

    const getProgressColor = (progress) => {
        if (progress >= 90) return "#ef4444";
        if (progress >= 70) return "#f59e0b";
        return "#22c55e";
    };

    useEffect(() => {
        fetchBudgets();
    }, []);

    return (
        <div className="shared-budgets-page">
            {/* Header */}
            <div className="sb-header">
                <div className="sb-header-left">
                    <h1>Shared Budgets</h1>
                    {pendingInvites.length > 0 && (
                        <span className="sb-invite-badge">
                            {pendingInvites.length} invite{pendingInvites.length > 1 ? "s" : ""}
                        </span>
                    )}
                </div>
                <button
                    className="sb-create-btn"
                    onClick={() => setShowCreateModal(true)}
                >
                    + Create Shared Budget
                </button>
            </div>

            {/* Stats */}
            <div className="sb-stats">
                <div className="sb-stat-card">
                    <span className="sb-stat-icon">🤝</span>
                    <div className="sb-stat-info">
                        <span className="sb-stat-value">{activeBudgets.length}</span>
                        <span className="sb-stat-label">Active Budgets</span>
                    </div>
                </div>
                <div className="sb-stat-card">
                    <span className="sb-stat-icon">💰</span>
                    <div className="sb-stat-info">
                        <span className="sb-stat-value">
                            ${formatCurrency(activeBudgets.reduce((sum, b) => sum + (parseFloat(b.total_amount) || 0), 0))}
                        </span>
                        <span className="sb-stat-label">Total Budget</span>
                    </div>
                </div>
                <div className="sb-stat-card">
                    <span className="sb-stat-icon">📊</span>
                    <div className="sb-stat-info">
                        <span className="sb-stat-value">
                            ${formatCurrency(activeBudgets.reduce((sum, b) => sum + (parseFloat(b.total_spent) || 0), 0))}
                        </span>
                        <span className="sb-stat-label">Total Spent</span>
                    </div>
                </div>
                <div className="sb-stat-card">
                    <span className="sb-stat-icon">📥</span>
                    <div className="sb-stat-info">
                        <span className="sb-stat-value">{pendingInvites.length}</span>
                        <span className="sb-stat-label">Pending Invites</span>
                    </div>
                </div>
            </div>

            {/* Pending Invites */}
            {pendingInvites.length > 0 && (
                <div className="sb-invites-section">
                    <h2>Pending Invitations</h2>
                    <div className="sb-invites-grid">
                        {pendingInvites.map((invite) => (
                            <div key={invite.id} className="sb-invite-card">
                                <div className="sb-invite-header">
                                    <div 
                                        className="sb-invite-avatar"
                                        style={{ backgroundColor: getAvatarColor(invite.invited_by.username) }}
                                    >
                                        {getInitials(invite.invited_by)}
                                    </div>
                                    <div className="sb-invite-info">
                                        <h3>{invite.budget_name}</h3>
                                        <p>
                                            Invited by{" "}
                                            <strong>
                                                {invite.invited_by.first_name || invite.invited_by.username}
                                            </strong>
                                        </p>
                                        <p className="sb-invite-amount">
                                            Budget: ${formatCurrency(invite.budget_amount)}
                                        </p>
                                    </div>
                                </div>
                                <div className="sb-invite-role">
                                    Role: <span className="sb-role-badge">{invite.role}</span>
                                </div>
                                {invite.message && (
                                    <p className="sb-invite-message">"{invite.message}"</p>
                                )}
                                <div className="sb-invite-actions">
                                    <button
                                        className="sb-accept-btn"
                                        onClick={() => handleRespondToInvite(invite.id, "accept")}
                                    >
                                        ✓ Accept
                                    </button>
                                    <button
                                        className="sb-decline-btn"
                                        onClick={() => handleRespondToInvite(invite.id, "decline")}
                                    >
                                        ✕ Decline
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div className="sb-tabs">
                <button
                    className={`sb-tab ${activeTab === "active" ? "active" : ""}`}
                    onClick={() => setActiveTab("active")}
                >
                    Active
                    <span className="sb-tab-count">{activeBudgets.length}</span>
                </button>
                <button
                    className={`sb-tab ${activeTab === "inactive" ? "active" : ""}`}
                    onClick={() => setActiveTab("inactive")}
                >
                    Archived
                    <span className="sb-tab-count">{inactiveBudgets.length}</span>
                </button>
            </div>

            {/* Budget Cards */}
            <div className="sb-content">
                {loading ? (
                    <div className="sb-loading">Loading share budgets...</div>
                ) : (activeTab === "active" ? activeBudgets : inactiveBudgets).length === 0 ? (
                    <div className="sb-empty">
                        <span className="sb-empty-icon">🤝</span>
                        <h3>
                            {activeTab === "active"
                                ? "No shared budgets yet"
                                : "No archived bugdets"}
                        </h3>
                        <p>
                            {activeTab === "active"
                                ? "Create a shared budget and invite friends to start tracking expenses together!"
                                : "Archived budgets will appear here."}
                        </p>
                        {activeTab === "active" && (
                            <button
                                className="sb-create-btn"
                                onClick={() => setShowCreateModal(true)}
                            >
                                + Create Shared Budget
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="sb-budget-grid">
                        {(activeTab === "active" ? activeBudgets : inactiveBudgets).map((budget) => (
                            <div
                                key={budget.id}
                                className="sb-budget-card"
                                onClick={() => navigate(`/shared-budgets/${budget.id}`)}
                            >
                                {/* Card Header */}
                                <div className="sb-card-header">
                                    <div className="sb-card-title-row">
                                        <h3>{budget.name}</h3>
                                        {budget.category && (
                                            <span className="sb-category-badge">
                                                {budget.category}
                                            </span>
                                        )}
                                    </div>
                                    <span className="sb-role-badge small">
                                        {budget.user_role}
                                    </span>
                                </div>

                                {/* Budget Progress */}
                                <div className="sb-card-progress">
                                    <div className="sb-progress-header">
                                        <span className="sb-spent">
                                            ${formatCurrency(budget.total_spent)}
                                        </span>
                                        <span className="sb-total">
                                            of ${formatCurrency(budget.total_amount)}
                                        </span>
                                    </div>
                                    <div className="sb-progress-bar">
                                        <div
                                            className="sb-progress-fill"
                                            style={{
                                                width: `${Math.min(budget.progress, 100)}%`,
                                                backgroundColor: getProgressColor(budget.progress),
                                            }}
                                        />
                                    </div>
                                    <div className="sb-progress-footer">
                                        <span className="sb-remaining">
                                            ${formatCurrency(budget.remaining)} remaining
                                        </span>
                                        <span className="sb-percentage">
                                            {budget.progress}%
                                        </span>
                                    </div>
                                </div>

                                {/* Members */}
                                <div className="sb-card-members">
                                    <div className="sb-avatar-stack">
                                        {budget.members.slice(0, 4).map((member) => (
                                            <div
                                                key={member.id}
                                                className="sb-member-avatar"
                                                style={{
                                                    backgroundColor: getAvatarColor(member.user.username),
                                                }}
                                                title={member.user.username}
                                            >
                                                {member.user.username?.slice(0, 1).toUpperCase()}
                                            </div>
                                        ))}
                                        {budget.member_count > 4 && (
                                            <div className="sb-member-avatar more">
                                                +{budget.member_count - 4}
                                            </div>
                                        )}
                                    </div>
                                    <span className="sb-member-count">
                                        {budget.member_count} member{budget.member_count > 1 ? "s" : ""}
                                    </span>
                                </div>

                                {/* Balance */}
                                <div className="sb-card-balance">
                                    <span className="sb-balance-label">Your Balance:</span>
                                    <span
                                        className={`sb-balance-value ${
                                            budget.user_balance > 0
                                                ? "positive"
                                                : budget.user_balance < 0
                                                ? "negative"
                                                : "neutral"
                                        }`}
                                    >
                                        {budget.user_balance > 0
                                            ? `You are owed $${formatCurrency(budget.user_balance)}`
                                            : budget.user_balance < 0
                                            ? `You owe $${formatCurrency(Math.abs(budget.user_balance))}`
                                            : "All settled ✓"}
                                    </span>
                                </div>
                                
                                {/* Dates */}
                                <div className="sb-card-dates">
                                    <span>{budget.start_date} → {budget.end_date} </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Modal */}
            {showCreateModal && (
                <CreateSharedBudgetModal
                    onClose={() => setShowCreateModal(false)}
                    onSave={handleCreateBudget}
                />
            )}
        </div>
    );
};

export default SharedBudgets;