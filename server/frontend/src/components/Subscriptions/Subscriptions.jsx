import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../utils/csrf';
import ExportButton from '../ExportButton/ExportButton';
import { EXPORT_CONFIGS } from '../../utils/export';
import { useToast } from '../Toast/ToastContext';
import SubscriptionCard from './SubscriptionCard';
import SubscriptionModal from './SubscriptionModal';
import './Subscriptions.css';


const Subscriptions = () => {
    const [ subscriptions, setSubscriptions ] = useState([]);
    const [ loading, setLoading ] = useState(true);
    const [ showModal, setShowModal ] = useState(false);
    const [ editingSubscription, setEditingSubscription ] = useState(null);
    const [ filter, setFilter ] = useState("all");

    const toast = useToast();
    const subscription_url = "/djangoapp/subscriptions";

    const fetchSubscriptions = useCallback(async () => {
        try {
            const response = await apiFetch(subscription_url, {
                method: "GET",
            });

            const data = await response.json();
            setSubscriptions(data.subscriptions || []);
        } catch (error) {
            console.error("Error fetching subscriptions:", error);
            toast.error("Failed to load subscriptions");
        } finally {
            setLoading(false);
        }
    }, [toast]);

    useEffect(() => {
        fetchSubscriptions();
    }, [fetchSubscriptions]);

    const handleCreate = async (subscriptionData) => {
        try {
            const response = await apiFetch(`${subscription_url}/create`, {
                method: "POST",
                body: JSON.stringify(subscriptionData),
            });

            if (response.ok) {
                fetchSubscriptions();
                setShowModal(false);
                toast.success("Subscription created");
            } else {
                toast.error("Failed to create subscription");
            }
        } catch (error) {
            console.error("Error creating subscription", error);
            toast.error("Something went wrong");
        }
    };

    const handleUpdate = async (id, subscriptionData) => {
        try {
            const response = await apiFetch(`${subscription_url}/${id}/update`, {
                method: "PATCH",
                body: JSON.stringify(subscriptionData),
            });

            if (response.ok) {
                fetchSubscriptions();
                setShowModal(false);
                setEditingSubscription(null);
                toast.success("Subscription updated");
            } else {
                toast.error("Failed to update subscription");
            }
        } catch (error) {
            console.error("Error updating subscription:", error);
            toast.error("Something went wrong");
        }
    };

    const handleStatusChange = async (id, newStatus) => {
        try {
            const response = await apiFetch(`${subscription_url}/${id}/status`, {
                method: "PATCH",
                body: JSON.stringify({ status: newStatus }),
            });

            if (response.ok) {
                setSubscriptions((prev) =>
                    prev.map((sub) =>
                        sub.id === id ? { ...sub, status: newStatus } : sub
                    )
                );
                toast.info(`Subscription ${newStatus}`);
            } else {
                toast.error("Failed to update status");
            }
        } catch (error) {
            console.error("Error updating status:", error);
            toast.error("Something went wrong");
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Delete this subscription?")) return;

        try {
            const response = await apiFetch(`${subscription_url}/${id}/delete`, {
                method: "DELETE",
            });

            if (response.ok) {
                setSubscriptions((prev) => prev.filter((sub) => sub.id !== id));
                toast.success("Subscription deleted");
            } else {
                toast.error("Failed to delete subscription");
            }
        } catch (error) {
            console.error("Error deleting subscription:", error);
            toast.error("Something went wrong");
        }
    };


    const handleEdit = (subscription) => {
        setEditingSubscription(subscription);
        setShowModal(true);
    };

    const handleTogglePayment = async (paymentId, subscriptionId) => {
        try {
            const response = await apiFetch(`/djangoapp/payments/${paymentId}/toggle`, {
                method: "PATCH",
            });

            if (response.ok) {
                const data = await response.json();
                // Update local state
                setSubscriptions((prev) =>
                    prev.map((sub) => {
                        if (sub.id === subscriptionId) {
                            return {
                                ...sub,
                                payments: sub.payments.map((p) =>
                                    p.id === paymentId ? { ...p, is_paid: data.payment.is_paid } : p
                                ),
                            };
                        }
                        return sub;
                    })
                );
            }
        } catch (error) {
            console.error("Error toggling payment:", error);
            toast.error("Failed to update payment");
        }
    };

    // Filter subscriptions
    const filteredSubscriptions =
        filter === "all"
            ? subscriptions
            : subscriptions.filter((sub) => sub.status === filter);

    // Calculate totals
    const totals = {
        active: subscriptions
            .filter((s) => s.status === "active")
            .reduce((sum, s) => sum + parseFloat(s.amount || 0), 0),
        paused: subscriptions
            .filter((s) => s.status === "paused")
            .reduce((sum, s) => sum + parseFloat(s.amount || 0), 0),
        cancelled: subscriptions
            .filter((s) => s.status === "cancelled").length,
    };
    
    // console.log("Subscriptions fetched:", subscriptions)

    return (
        <div className="subscriptions-page">
            <div className="subscriptions-header">
                <h1>Subscriptions</h1>
                <div className="subscriptions-header-actions">
                    <ExportButton
                        data={filteredSubscriptions}
                        columns={EXPORT_CONFIGS.subscriptions.columns}
                        title={EXPORT_CONFIGS.subscriptions.getTitle()}
                        subtitle={`${filteredSubscriptions.length} subscriptions - ${filter}`}
                        filename={EXPORT_CONFIGS.subscriptions.getFilename()}
                        summary={[
                            {
                                label: "Active Monthly",
                                value: `$${totals.active.toFixed(2)}`,
                                color: [34, 197, 94],
                            },
                            {
                                label: "Paused Monthly",
                                value: `$${totals.paused.toFixed(2)}`,
                                color: [245, 158, 11],
                            },
                            {
                                label: "Cancelled",
                                value: String(totals.cancelled),
                                color: [239, 68, 68],
                            },
                        ]}
                        onExport={(status, message) => {
                            if (status === "success") toast.success(message);
                            else toast.error(message);
                        }}
                    />
                    <button
                        className="subscriptions-add-btn"
                        onClick={() => {
                            setEditingSubscription(null);
                            setShowModal(true);
                        }}
                    >
                        + Add Subscription
                    </button>
                </div>
            </div>

            {/* Summary Cards */}

            <div className="subscriptions-summary">
                <div className="sub-summary-card active">
                    <span className="label">Active Monthly</span>
                    <span className="value">${totals.active.toFixed(2)}</span>
                </div>
                <div className="sub-summary-card paused">
                    <span className="label">Paused Monthly</span>
                    <span className="value">${totals.paused.toFixed(2)}</span>
                </div>
                <div className="sub-summary-card cancelled">
                    <span className="label">Cancelled</span>
                    <span className="value">{totals.cancelled}</span>
                </div>
            </div>

            {/* Filter tabs */}
            <div className="filter-tabs">
                {["all", "active", "paused", "cancelled"].map((status) => (
                    <button
                        key={status}
                        className={`filter-tab ${filter === status ? "active" : ""}`}
                        onClick={() => setFilter(status)}
                    >
                        {status.charAt(0).toUpperCase() + status.slice(1)}
                        <span className="count">
                            {status === "all"
                                ? subscriptions.length
                                : subscriptions.filter((s) => s.status === status).length}
                        </span>
                    </button>
                ))}
            </div>

            {/*  Subscriptions list */}
            <div className="subscriptions-list">
                {loading ? (
                    <p className="loading-state">Loading subscriptions...</p>
                ) : filteredSubscriptions.length === 0 ? (
                    <p className="empty-state">No subscriptions found.</p>
                ) : (
                    filteredSubscriptions.map((subscription) => (
                        <SubscriptionCard
                            key={subscription.id}
                            subscription={subscription}
                            onEdit={() => handleEdit(subscription)}
                            onDelete={() => handleDelete(subscription.id)}
                            onStatusChange={(status) =>
                                handleStatusChange(subscription.id, status)
                            }
                            onTogglePayment={(paymentId) =>
                                handleTogglePayment(paymentId, subscription.id)
                            }
                        />
                    ))
                )}
            </div>

            {/* Modal */}
            {showModal && (
                <SubscriptionModal
                    subscription={editingSubscription}
                    onClose={() => {
                        setShowModal(false);
                        setEditingSubscription(null);
                    }}
                    onSave={(data) => {
                        if (editingSubscription) {
                            handleUpdate(editingSubscription.id, data);
                        } else {
                            handleCreate(data);
                        }
                    }}
                />
            )}
        </div>
    );
};

export default Subscriptions;