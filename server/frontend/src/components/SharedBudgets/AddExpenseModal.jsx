import React, { useState } from 'react';

const AddExpenseModal = ({ members, splitType, onClose, onSave }) => {
    const [ formData, setFormData ] = useState({
        description: "",
        amount: "",
        paid_by_id: "",
        date: new Date().toISOString().split('T')[0],
        category: "",
        notes: "",
        split_type: splitType || "equal",
    });
    const [ customSplits, setCustomSplits ] = useState({});
    const [ errors, setErrors ] = useState({});

    const safeMembers = Array.isArray(members) ? members : [];

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
        if (errors[name]) {
            setErrors((prev) => ({ ...prev, [name]: "" }));
        }
    };

    const handleCustomSplitChange = (userId, amount) => {
        setCustomSplits((prev) => ({ ...prev, [userId]: amount }));
    };

    const validate = () => {
        const newErrors = {};
        if (!formData.description.trim()) newErrors.description = "Description is required";
        if (!formData.amount || parseFloat(formData.amount) <= 0) {
            newErrors.amount = "Enter a valid amount";
        }
        if (!formData.paid_by_id) newErrors.paid_by_id = "Select who paid";
        if (!formData.date) newErrors.date = "Date is required";

        if (formData.split_type === "custom") {
            const totalSplit = Object.values(customSplits).reduce(
                (sum, val) => sum + (parseFloat(val) || 0), 0
            );
            if (Math.abs(totalSplit - parseFloat(formData.amount)) > 0.01) {
                newErrors.splits = `Split total (
                $${totalSplit.toFixed(2)}) must equal expense amount (
                $${parseFloat(formData.amount).toFixed(2)})`;
            }
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!validate()) return;

        const data = {
            ...formData,
            amount: parseFloat(formData.amount),
            paid_by_id: parseInt(formData.paid_by_id),
        };

        if (formData.split_type === "custom") {
            data.splits = Object.entries(customSplits).map(([userId, amount]) => ({
                user_id: parseInt(userId),
                amount: parseFloat(amount) || 0,
            }));
        }

        onSave(data);
    };

    const distributeEvenly = () => {
        const amount = parseFloat(formData.amount) || 0;
        const perPerson = amount / safeMembers.length;
        const newSplits = {};
        safeMembers.forEach((m) => {
            newSplits[m.user.id] = perPerson.toFixed(2);
        });
        setCustomSplits(newSplits);
    };

    return (
        <div className="modal-overal" onClick={onClose}>
            <div className="modal-content sb-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Add Expense</h2>
                    <button className="modal-close-btn" onClick={onClose}>×</button>
                </div>

                <form onSubmit={handleSubmit} className="sb-modal-form">
                    {/* Description */}
                    <div className="sb-form-group">
                        <label>Description</label>
                        <input
                            type="text"
                            name="description"
                            value={formData.description}
                            onChange={handleChange}
                            placeholder="e.g., Groceries, Electricity Bill"
                            className={errors.description ? "error" : ""}
                        />
                        {errors.description && <span className="sb-error">{errors.description}</span>}
                    </div>

                    {/* Amount & Paid By */}
                    <div className="sb-form-row">
                        <div className="sb-form-group">
                            <label>Amount *</label>
                            <input
                                type="number"
                                name="amount"
                                value={formData.amount}
                                onChange={handleChange}
                                placeholder="0.00"
                                step="0.01"
                                min="0"
                                className={errors.amount ? "error" : ""}
                            />
                            {errors.amount && <span className="sb-error">{errors.amount}</span>}
                        </div>
                        <div className="sb-form-group">
                            <label>Paid By</label>
                            <select
                                name="paid_by_id"
                                value={formData.paid_by_id}
                                onChange={handleChange}
                                className={errors.paid_by_id ? "error" : ""}
                            >
                                <option value="">Select who paid</option>
                                {safeMembers.map((member) => (
                                    <option key={member.user.id} value={member.user.id}>
                                        {member.user.first_name || member.user.username}
                                    </option>
                                ))}
                            </select>
                            {errors.paid_by_id && <span className="sb-error">{errors.paid_by_id}</span>}
                        </div>
                    </div>

                    {/* Date & Category */}
                    <div className="sb-form-row">
                        <div className="sb-form-group">
                            <label>Date *</label>
                            <input
                                type="date"
                                name="date"
                                value={formData.date}
                                onChange={handleChange}
                                className={errors.date ? "error" : ""}
                            />
                        </div>
                        <div className="sb-form-group">
                            <label>Category</label>
                            <input
                                type="text"
                                name="category"
                                value={formData.category}
                                onChange={handleChange}
                                placeholder="e.g., Food, Utilities"
                            />
                        </div>
                    </div>

                    {/* Split Type */}
                    <div className="sb-form-group">
                        <label>Split Type</label>
                        <select
                            name="split_type"
                            value={formData.split_type}
                            onChange={handleChange}
                        >
                            <option value="equal">Equal Split</option>
                            <option value="percentage">By Percentage</option>
                            <option value="custom">Custom Amount</option>
                        </select>
                    </div>

                    {/* Custom Splits */}
                    {formData.split_type === "custom" && (
                        <div className="sb-form-group">
                            <div className="sb-splits-header">
                                <label>Custom Split</label>
                                <button
                                    type="button"
                                    className="sb-preset-btn small"
                                    onClick={distributeEvenly}
                                >
                                    Split Evenly
                                </button>
                            </div>
                            <div className="sb-custom-splits">
                                {safeMembers.map((member) => (
                                    <div key={member.user.id} className="sb-split-row">
                                        <span className="sb-split-name">
                                            {member.user.first_name || member.user.username}
                                        </span>
                                        <input
                                            type="number"
                                            step="0.01"
                                            min="0"
                                            placeholder="0.00"
                                            value={customSplits[member.iser.id] || ""}
                                            onChange={(e) =>
                                                handleCustomSplitChange(member.user.id, e.target.value)
                                            }
                                        />
                                    </div>
                                ))}
                            </div>
                            {errors.splits && <span className="sb-error">{errors.split}</span>}
                        </div>
                    )}

                    {/* Notes */}
                    <div className="sb-form-group">
                        <label>Notes</label>
                        <textarea
                            name="notes"
                            value={formData.notes}
                            onChange={handleChange}
                            placeholder="Optional notes..."
                            rows="2"
                        />
                    </div>

                    {/* Actions */}
                    <div className="sb-modal-actions">
                        <button type="button" className="sb-cancel-btn" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="sb-save-btn">
                            Add Expense
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddExpenseModal;