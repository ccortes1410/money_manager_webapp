import { useContext, useState, useEffect } from 'react';
import { AuthContext } from '../../AuthContext';
import SubscriptionCard from './SubscriptionCard';
import SubscriptionModal from './SubscriptionModal';
import './Subscriptions.css';


const Subscriptions = () => {
    const { user } = useContext(AuthContext);
    const [ subscriptions, setSubscriptions ] = useState([]);
    const [ loading, setLoading ] = useState(true);
    const [ showModal, setShowModal ] = useState(false);
    const [ editingSubscription, setEditingSubscription ] = useState(null);
    const [ filter, setFilter ] = useState("all");

    // const [ nameInput, setNameInput ] = useState("");
    // const [ amountInput, setAmountInput ] = useState("");
    // const [ dateInput, setDateInput ] = useState("");
    // const [ descriptionInput, setDescriptionInput ] = useState("");
    // const [ categoryInput, setCategoryInput ] = useState("");
    // const [ billingCycleInput, setBillingCycleInput ] = useState("");
    // const [ billingDayInput, setBillingDayInput ] = useState("");
    // const [ startDateInput, setStartDateInput ] = useState("");
    // const [ subscriptions, setSubscriptions ] = useState([]);
    // const { user } = useContext(AuthContext);
    // const [ selectedSubs, setSelectedSubs ] = useState([]);

    const BILLING_CYCLE_OPTIONS = [
        { value: "daily", label: "Daily" },
        { value: "weekly", label: "Weekly" },
        { value: "monthly", label: "Monthly" },
        { value: "yearly", label: "Yearly" },
    ];

    const getToday = () => {
        const today = new Date();
        return today.toISOString().split('T')[0];
    }

    const subscription_url = "/djangoapp/subscriptions";
    // const addSubscription_url = "/djangoapp/addSubscription";

    useEffect(() => {
        fetchSubscriptions();
    }, []);

    const fetchSubscriptions = async () => {
        try {
            const response = await fetch(subscription_url, {
                method: "GET",
                credentials: "include",
            });

            const data = await response.json();
            setSubscriptions(data.subscriptions || []);
        } catch (error) {
            console.error("Error fetching subscriptions");
        } finally {
            setLoading(false);
        }
    }

    const handleCreate = async (subscriptionData) => {
        try {
            const response = await fetch(subscription_url+'/create', {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json"},
                body: JSON.stringify(subscriptionData),
            });

            if (response.ok) {
                fetchSubscriptions();
                setShowModal(false);
            }
        } catch (error) {
            console.error("Error creating subscription", error);
        }
    };

    const handleUpdate = async (id, subscriptionData) => {
        try {
            const response = await fetch(subscription_url+`/${id}/update`, {
                method: "PATCH",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(subscriptionData),
            });

            if (response.ok) {
                fetchSubscriptions();
                setShowModal(false);
                setEditingSubscription(null);
            }
        } catch (error) {
            console.error("Error updating subscription:", error);
        }
    };

    const handleStatusChange = async (id, newStatus) => {
        try {
            const response = await fetch(subscription_url+`/${id}/status`, {
                method: "PATCH",
                credentials: "include",
                headers: { "Content-Type": "aplication/json" },
                body: JSON.stringify({ status: newStatus }),
            });

            if (response.ok) {
                setSubscriptions((prev) =>
                prev.map((sub) =>
                    sub.id === id ? { ...sub, status: newStatus } : sub
                )
            );
            }
        } catch (error) {
            console.error("Error updating status:", error);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Delete this subscription?")) return;

        try {
            const response = await fetch(subscription_url+`/${id}/delete`, {
                method: "DELETE",
                credentials: "include",
            });

            if (response.ok) {
                setSubscriptions((prev) => prev.filter((sub) => sub.id !== id));
            }
        } catch (error) {
            console.error("Error deleting subscription:", error);
        }
    };


    const handleEdit = (subscription) => {
        setEditingSubscription(subscription);
        setShowModal(true);
    }

    const handleTogglePayment = async (paymentId, subscriptionId) => {
        try {
            const response = await fetch(`/djangoapp/payments/${paymentId}/toggle`, {
                method: "PATCH",
                credentials: "include",
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
            .reduce((sum, s) => sum + s.amount, 0),
        paused: subscriptions
            .filter((s) => s.status === "paused")
            .reduce((sum, s) => sum + s.amount, 0),
        cancelled: subscriptions
            .filter((s) => s.status === "cancelled").length,
    };
    
    console.log("Subscriptions fetched:", subscriptions)

    return (
        <div className="subscriptions-page">
            <div className="subscriptions-header">
                <h1>Subscriptions</h1>
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
                {filteredSubscriptions.length === 0 ? (
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