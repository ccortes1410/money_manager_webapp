

const BudgetsCard = ({ budgets, period }) => {
    const {
        total_budgeted = 0,
        total_spent = 0,
        remaining = 0,
        percent_used = 0
    } = budgets;

    const isOverBudget = remaining< 0;

    return (
        <div className="card">
            <h3>Budgets ({period})</h3>

            <div className="budget-summary">
                <div className="budget-stat">
                    <span>Budgeted</span>
                    <span>${total_budgeted.toFixed(0)}</span>
                </div>

                <div className="budget-stat">
                    <span>Spent</span>
                    <span>${total_spent.toFixed(0)}</span>
                </div>

                <div className={`{budget-stat ${isOverBudget ? "over" : "under"}`}>
                    <span>Remaining</span>
                    <span>${remaining.toFixed(0)}</span>
                </div>

                <div className="budget-progress">
                    <div
                        className={`progress-bar ${isOverBudget ? "over" : ""}`}
                        style={{ width: `${Math.min(percent_used, 100)}%`}}
                    />
                </div>
                <p className="percent-label">{percent_used}% used</p>
            </div>
        </div>
    );
};

export default BudgetsCard;