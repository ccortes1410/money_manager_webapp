import React, { useState } from 'react';

const SettleUpModal = ({ debts, userId, onClose, onSave }) => {
    const [ selectedDebt, setSelectedDebt ] = useState(null);
    const [ amount, setAmount ] = useState("");
    const [ date, setDate ] = useState(new Date().toISOString().split('T')[0]);
    const [ notes, setNotes ] = useState("");
    const [ error, setError ] = useState("");

    const safeDebts = Array.isArray(debts) ? debts : [];
    const userDebts = safeDebts.filter((d) => d.from_user.id === userId);

    const handleSelectDebt = (debt) => {
        setSelectedDebt(debt);
        setAmount(debt.amount.toFixed(2));
        setError("");
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setError("");

        if (!selectedDebt) {
            setError("Select a debt to settle");
            return;
        }

        const settleAmount = parseFloat(amount);
        if (!settleAmount || settleAmount <=0) {
            setError("Enter a valid amount");
            return;
        }

        onSave({
            receiver_id: selectedDebt.to_user.id,
            amount: settleAmount,
            date: date,
            notes: notes,
        });
    };

    const getAvatarColor = (username) => {
        const colors = [
            "#3b82f6",
            "#22c55e",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
            "#ec4899"
        ];
        if (!username) return colors[0];
        return colors[username.charAt(0) & colors.length];
    };

    return (
        <div className="modal-overlay" onClick={(onClose)}>
            <div className="modal-content sb-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>💰 Settle Up</h2>
                    <button className="modal-close-btn" onClick={onClose}>×</button>
                </div>

                <div className="sb-modal-form">
                    {userDebts.length === 0 ? (
                        <div className="sb-settle-empty">
                            <span className="sb-settled-icon">✅</span>
                            <h3>You're all settled!</h3>
                            <p>You don't owe anyone right now.</p>
                            <button className="sb-cancel-btn" onClick={onClose}>
                                Close
                            </button>
                        </div>
                    ) : (
                        <>
                            {/* Debt Selection */}
                            <div className="sb-form-group">
                                <label>Select who to pay</label>
                                <div className="sb-debt-options">
                                    {userDebts.map((debt, index) => (
                                        <div
                                            key={index}
                                            className={`sb-debt-option ${
                                                selectedDebt === debt ? "selected" : ""
                                            }`}
                                            onClick={() => handleSelectDebt(debt)}
                                        >
                                            <div
                                                className="sb-debt-option-avatar"
                                                style={{
                                                    backgroundColor: getAvatarColor(debt.to_user.username),
                                                }}
                                            >
                                                {debt.to_user.username?.slice(0, 1).toUpperCase()}
                                            </div>
                                            <div className="sb-debt-option-info">
                                                <span className="sb-debt-option-name">
                                                    {debt.to_user.first_name || debt.to_user.username}
                                                </span>
                                                <span className="sb-debt-option-amount">
                                                    You owe ${debt.amount.toFixed(2)}
                                                </span>
                                            </div>
                                            {selectedDebt === debt && (
                                                <span className="sb-debt-check">✓</span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Settlement Form */}
                            {selectedDebt && (
                                <form onSubmit={handleSubmit}>
                                    {/* Payment Summary */}
                                    <div className="sb-settle-summary">
                                        <span>
                                            Paying{" "}
                                            <strong>
                                                {selectedDebt.to_user.first_name || selectedDebt.to_user.username}
                                            </strong>
                                        </span>
                                    </div>

                                    <div className="sb-form-row">
                                        <div className="sb-form-group">
                                            <label>Amount *</label>
                                            <input
                                                type="number"
                                                step="0.01"
                                                min="0"
                                                value={amount}
                                                onChange={(e) => setAmount(e.target.value)}
                                                placeholder="0.00"
                                            />
                                        </div>
                                        <div className="sb-form-group">
                                            <label>Date</label>
                                            <input
                                                type="date"
                                                value={date}
                                                onChange={(e) => setDate(e.target.value)}
                                            />
                                        </div>
                                    </div>

                                    <div className="sb-form-group">
                                        <label>Payment Method / Notes</label>
                                        <input
                                            type="text"
                                            value={notes}
                                            onChange={(e) => setNotes(e.target.value)}
                                            placeholder="e.g., Venmo, Cash, Bank transfer"
                                        />
                                    </div>

                                    {/* Quick Amount Button */}
                                    <div className="sb-quicka-amounts">
                                        <button
                                            type="button"
                                            className="sb-preset-btn small"
                                            onClick={() => setAmount(selectedDebt.amount.toFixed(2))}
                                        >
                                            Full Amount (${selectedDebt.amount.toFixed(2)})
                                        </button>
                                        <button
                                            type="button"
                                            className="sb-preset-btn small"
                                            onClick={() => setAmount((selectedDebt.amount / 2).toFixed(2))}
                                        >
                                            Half (${(selectedDebt.amount / 2).toFixed(2)})
                                        </button>
                                    </div>

                                    {error && <div className="sb-error-message">{error}</div>}

                                    <div className="sb-modal-actions">
                                        <button type="button" className="sb-cancel-btn" onClick={onClose}>
                                            Cancel
                                        </button>
                                        <button type="submit" className="sb-save-btn">
                                            💰 Record Payment
                                        </button>
                                    </div>
                                </form>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SettleUpModal;