import { useState, useEffect } from "react";
import "./SubscriptionModal.css"

const SubscriptionModal = ({ subscription, onClose, onSave }) => {
    const [ formData, setFormData ] = useState({
        name: "",
        amount: "",
        category: "",
        billing_cycle: "monthly",
        billing_day: 1,
        start_date: new Date().toISOString().split("T")[0],
        description: "",
        status: "active",
    });

    useEffect(() => {
        if (subscription) {
            setFormData({
                name: subscription.name || "",
                amount: subscription.amount || "",
                category: subscription.category || "",
                billing_cycle: subscription.billing_cycle || "monthly",
                billing_day: subscription.billing_day || 1,
                start_date: subscription.start_date || "",
                description: subscription.description || "",
                status: subscription.status || "active",
            });
        }
    }, [subscription]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave({
            ...formData,
            amount: parseFloat(formData.amount),
            billing_day: parseInt(formData.billing_day),
        });
    };

    return (        
    <div className="modal-overlay" onClick={onClose}>
        <div className="subscriptions-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
                <h2>{subscription ? "Edit Subscription" : "New Subscription"}</h2>
                <button className="close-btn" onClick={onClose}>
                    ×
                </button>
            </div>

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="name">Name *</label>
                    <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        placeholder="Netflix, Spotify, etc."
                        required
                    />
                </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="amount">Amount *</label>
                            <input
                                type="number"
                                id="amount"
                                name="amount"
                                value={formData.amount}
                                onChange={handleChange}
                                placeholder="9.99"
                                step="0.01"
                                min="0"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="billing_cycle">Billing Cycle</label>
                            <select
                                id="billing_cycle"
                                name="billing_cycle"
                                value={formData.billing_cycle}
                                onChange={handleChange}
                            >
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                                <option value="yearly">Yearly</option>
                            </select>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="billing_day">Billing Day</label>
                            <input
                                type="number"
                                id="billing_day"
                                name="billing_day"
                                value={formData.billing_day}
                                onChange={handleChange}
                                min="1"
                                max="31"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="category">Category *</label>
                            <input
                                type="text"
                                id="category"
                                name="category"
                                value={formData.category}
                                onChange={handleChange}
                                placeholder="Entertainment, Software, etc."
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="start_date">Start Date *</label>
                        <input
                            type="date"
                            id="start_date"
                            name="start_date"
                            value={formData.start_date}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="description">Description</label>
                        <textarea
                            id="description"
                            name="description"
                            value={formData.description}
                            onChange={handleChange}
                            placeholder="Optional notes..."
                            rows="3"
                        />
                    </div>

                    {subscription && (
                        <div className="form-group">
                            <label htmlFor="status">Status</label>
                            <select
                                id="status"
                                name="status"
                                value={formData.status}
                                onChange={handleChange}
                            >
                                <option value="active">Active</option>
                                <option value="paused">Paused</option>
                                <option value="cancelled">Cancelled</option>
                            </select>
                        </div>
                    )}

                    <div className="modal-actions">
                        <button type="button" className="cancel-btn" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="save-btn">
                            {subscription ? "Update" : "Create"}                                
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default SubscriptionModal;