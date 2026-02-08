import { useState } from 'react';
import "./SubscriptionCard.css";

const SubscriptionCard = ({
    subscription,
    onEdit,
    onDelete,
    onStatusChange,
    onTogglePayment,
}) => {
    const [ showPayments, setShowPayments ] = useState(false);

    const getStatusColor = (status) => {
        switch (status) {
            case "active":
                return "#27ae60";
            case "paused":
                return "#f39c12";
            case "cancelled":
                return "#e74c3c";
            default:
                return "#888";
        }
    };

    const getBillingLabel = (cycle) => {
        switch (cycle) {
            case "daily":
                return "/day";
            case "weekly":
                return "/week";
            case "monthly":
                return "/month";
            case "yearly":
                return "/year";
            default:
                return "";
        }
    };


    return (
        <div className={`subscription-card ${subscription.status}`}>
            <div className="card-header">
                <div className="card-title">
                    <h3>{subscription.name}</h3>
                    <span 
                        className="status-badge"
                        style={{ backgroundColor: getStatusColor(subscription.status) }}
                    >
                        {subscription.status}
                    </span>
                </div>
                <div className="card-amount">
                    <span className="amount">${(subscription.amount || 0).toFixed(2)}</span>
                    <span className="cycle">{getBillingLabel(subscription.billing_cycle)}</span>
                </div>
            </div>

            <div className="card-details">
                {subscription.category && (
                    <span className="detail">
                        <span className="label">Category:</span> {subscription.category}
                    </span>
                )}
                <span className="detail">
                    <span className="label">Billing day:</span> {subscription.billing_day}
                </span>
                <span className="detail">
                    <span className="label">Started:</span> {subscription.end_date}
                </span>
                {subscription.end_date && (
                    <span className="detail">
                        <span className="label">Ended:</span> {subscription.end_date}
                    </span>
                )}
            </div>

            {/* Status actions */}
            <div className="status-actions">
                {subscription.status !== "active" && (
                    <button
                        className="status-btn activate"
                        onClick={() => onStatusChange("active")}
                    >
                        Activate
                    </button>
                )}
                {subscription.status === "active" && (
                    <button
                        className="status-btn pause"
                        onClick={() => onStatusChange("paused")}
                    >
                        Pause
                    </button>
                )}
                {subscription.status !== "cancelled" && (
                    <button
                        className="status-btn cancel"
                        onClick={() => onStatusChange("cancelled")}
                    >
                        Cancel
                    </button>
                )}
            </div>

            {/* Payments Section */}
            <div className="payments-section">
                <button
                    className="toggle-payments"
                    onClick={() => setShowPayments(!showPayments)}
                >
                    {showPayments ? "Hide" : "Show"} Payments ({subscription.payment_count})
                </button>
                
                {showPayments && (
                    <div className="payments-list">
                        {subscription.payments.length === 0 ? (
                            <p className="no-payments">No payments recorded yet.</p>
                        ) : (
                            subscription.payments.map((payment) => (
                                <div
                                    key={payment.id}
                                    className={`payment-item ${payment.is_paid ? "paid" : "unpaid"}`}
                                >
                                    <span className="payment-date">{payment.date}</span>
                                    <span className="payment-amount">
                                        ${payment.amount.toFixed(2)}
                                    </span>
                                    <button
                                        className={`payment-status ${payment.is_paid ? "paid" : "unpaid"}`}
                                        onClick={() => onTogglePayment(payment.id)}
                                    >
                                        {payment.is_paid ? "✓ Paid" : "Mark Paid"}
                                    </button>
                                </div>
                            ))
                        )}
                        <div className="payment-total">
                            <span>Total paid:</span>
                            <strong>${subscription.total_paid.toFixed(2)}</strong>
                        </div>
                    </div>
                )}
            </div>

            {/* Card actions */}
            <div className="card-actions">
                <button className="edit-btn" onClick={onEdit}>
                    Edit
                </button>
                <button className="delete-btn" onClick={onDelete}>
                    Delete
                </button>
            </div>
        </div>
    );
};

export default SubscriptionCard;