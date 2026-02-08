
const BudgetCard = ({ budget, isSelected, onSelect, onEdit, onDelete, onToggleRecurring }) => {
    // const { 
    //     category,
    //     amount,
    //     spent,
    //     percentUsed,
    //     isOver,
    //     period_start,
    //     period_end,
    //     recurrence,
    //     is_recurring,
    // } = budget;
    const parseAmount = (value) => {
        if (value === null || value === undefined) return 0;
        const parsed = parseFloat(value);
        return isNaN(parsed) ? 0 : parsed;
    };

    // Safely extract values with defaults
    const category = budget?.category || 'Unknown';
    const amount = parseAmount(budget?.amount);
    const spent = parseAmount(budget?.spent);
    const remaining = parseAmount(budget?.remaining) || (amount - spent);
    const percentUsed = parseAmount(budget?.percentUsed) || (amount > 0 ? (spent / amount) * 100 : 0);
    const isOver = budget?.isOver ?? remaining < 0;
    const period_start = budget?.period_start || 'N/A';
    const period_end = budget?.period_end || 'N/A';
    const recurrence = budget?.recurrence || 'monthly';
    const is_recurring = budget?.is_recurring || false;

    console.log("Budget recevied in BudgetCard:", budget)
    console.log("Spent in BudgetCard:", spent);
    return (
        <div
            className={`budget-card ${isSelected ? "selected" : ""} ${isOver ? "over-budget" : "on-track"}`}
            onClick={onSelect}
        >
            <div className="budget-card-header">
                <h3 className="budget-category">{category}</h3>
                <div className="budget-actions">
                    <button
                        className={`recurring-btn ${is_recurring ? "active" : ""}`}
                        onClick={(e) => {
                            e.stopPropagation();
                            onToggleRecurring(!is_recurring);
                        }}
                        title={is_recurring ? 'Stop Recurring' : 'Make Recurring'}
                    >
                        🔄
                    </button>
                    <button
                        className="edit-btn"
                        onClick={(e) => {
                            e.stopPropagation();
                            onEdit();
                        }}
                    >
                        ✏️
                    </button>
                    <button
                        className="delete-btn"
                        onClick={(e) => {
                            e.stopPropagation();
                            onDelete();
                        }}
                    >
                        🗑️
                    </button>
                </div>
            </div>

            <div className="budget-card-body">
                <div className="budget-amounts">
                    <div className="amount-row">
                        <span className="label">Budget</span>
                        <span className="value">${amount.toFixed(2)}</span>
                    </div>
                    <div className="amount-row">
                        <span className="label">Spent</span>
                        <span className={`value ${isOver ? "over" : ""}`}>
                            ${spent.toFixed(2)}
                        </span>
                    </div>
                    <div className="amount-row">
                        <span className="label">{isOver ? "Over by" : "Remaining"}</span>
                        <span className={`value ${isOver ? "over" : "remaining"}`}>
                            ${Math.abs(remaining).toFixed(2)}
                        </span>
                    </div>
                </div>
            </div>

            {/* Progress Bar */}
            <div className="budget-progress">
                <div className="budget-progress-bar">
                    <div
                        className={`budget-progress-fill ${isOver ? "over" : "remaining"}`}
                        style={{ width: `${Math.min(percentUsed, 100)}%` }}
                    />
                    <span className={`budget-progress-percent ${isOver ? "over" : ""}`} style={{ width: `${Math.min(percentUsed, 100)}%` }}>
                        {percentUsed.toFixed(0)}%
                    </span>
                </div>

                {/* Period Info */}
                <div className="budget-period">
                    <span className="period-dates">
                        {period_start} - {period_end}
                    </span>
                    <div className="budget-badges">
                        {is_recurring && (
                            <span className="recurring-badge active">
                                🔄 {recurrence}
                            </span>
                        )}
                        {!is_recurring && recurrence && (
                            <span className="recurrence-badge">{recurrence}</span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BudgetCard;