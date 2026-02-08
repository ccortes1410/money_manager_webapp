import { useState, useEffect } from "react";

const BudgetModal = ({ budget, onClose, onSave }) => {
    const [formData, setFormData] = useState({
        category: "",
        amount: "",
        period_start: "",
        period_end: "",
        recurrence: "",
    });

    useEffect(() => {
        if (budget) {
            setFormData({
                category: budget.category || "",
                amount: budget.amount || "",
                period_start: budget.period_start || "",
                period_end: budget.period_end || "",
                recurrence: budget.recurrence || "",
            });
        }
    }, [budget]);
    
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
        });
    };

    return (
        <div className="budgets-modal-overlay" onClick={onClose}>
            <div className="budgets-modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="budgets-modal-header">
                    <h2>{budget ? "Edit Budget" : "Add Budget"}</h2>
                    <button className="budgets-modal-close-btn" onClick={onClose}>
                        ×
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="budgets-modal-form">
                    <div className="budgets-form-group">
                        <label htmlFor="category">Category</label>
                        <input
                            type="text"
                            id="category"
                            name="category"
                            value={formData.category}
                            onChange={handleChange}
                            placeholder="e.g., Groceries, Entertainment"
                            required
                        />
                    </div>

                    <div className="budgets-form-group">
                        <label htmlFor="amount">Amount</label>
                        <input
                            type="number"
                            id="amount"
                            name="amount"
                            value={formData.amount}
                            onChange={handleChange}
                            placeholder="0.00"
                            step="0.01"
                            min="0"
                            required
                        />
                    </div>

                    <div className="budgets-form-row">
                        <div className="budgets-form-group">
                            <label htmlFor="period_start">Start Date</label>
                            <input
                                type="date"
                                id="period_start"
                                name="period_start"
                                value={formData.period_start}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="budgets-form-group">
                            <label htmlFor="period_end">End Date</label>
                            <input
                                type="date"
                                id="period_end"
                                name="period_end"
                                value={formData.period_end}
                                onChange={handleChange}
                                required
                            />
                        </div>
                    </div>

                    <div className="budgets-form-group">
                        <label htmlFor="recurrence">Recurrence</label>
                        <select
                            id="recurrence"
                            name="recurrence"
                            value={formData.recurrence}
                            onChange={handleChange}
                        >
                            <option value="">No Recurrence</option>
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="monthly">Monthly</option>
                            <option value="yearly">Yearly</option>
                        </select>
                    </div>

                    <div className="budgets-modal-actions">
                        <button type="button" className="budgets-cancel-btn" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="budgets-save-btn">
                            {budget ? "Update" : "Create"}
                        </button>
                    </div>     
                </form>
            </div>
        </div>
    );
};

export default BudgetModal;