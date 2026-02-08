import './Budgets.css';


const Budget = ({ budget }) => {

    if (!budget) {
        return (
            <div className="budget-details empty">
                <p>Select a budget to view details.</p>
            </div>
        );
    }

    const parseAmount = (value) => {
        if (value === null || value === undefined) return 0;
        const parsed = parseFloat(value);
        return isNaN(parsed) ? 0 : parsed;
    };

    //  Calculate values with safe defaults
    const amount = parseAmount(budget.amount);
    const spent = parseAmount(budget.spent);
    const transactionSpent = parseAmount(budget.transaction_spent);
    const subscriptionSpent = parseAmount(budget.subscription_spent);
    const remaining = parseAmount(budget.remaining);
    const isOver = remaining < 0;
    const percentUsed = amount > 0 ? (spent / amount) * 100 : 0;
    
    const transactions = Array.isArray(budget.transactions) ? budget.transactions : [];
    const subscriptions = Array.isArray(budget.subscriptions) ? budget.subscriptions : [];

    console.log("Budget data:", {
        raw_amount: budget.amount,
        raw_spent: budget.spent,
        parsed_amount: amount,
        parsed_spent: spent,
        remaining,
        percentUsed
    });

    return (
        <div className="budget-details">
            {/* Header */}
            <div className="budget-details-header">
                <h3>{budget.category}</h3>
                {budget.recurrence && (
                    <span className="recurrence-badge">{budget.recurrence}</span>
                )}
            </div>

            {/* Stats in a row */}
            <div className="budget-stats-grid">
                <div className="stat-item">
                    <span className="stat-label">Budget</span>
                    <span className="stat-value">${(amount || 0).toFixed(2)}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Spent</span>
                    <span className={`stat-value ${isOver ? 'over' : ''}`}>
                        ${spent.toFixed(2)}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">{isOver ? 'Over by' : 'Remaining'}</span>
                    <span className={`stat-value ${isOver ? 'over' : 'remaining'}`}>
                        ${Math.abs(remaining).toFixed(2)}
                    </span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Used</span>
                    <span className={`stat-value ${isOver ? 'over' : ''}`}>
                        {percentUsed.toFixed(1)}%
                    </span>
                </div>
            </div>
            
            {/* Spending Breakdown */}
            <div className="bd-spending-breakdown">
                <div className="bd-breakdown-item">
                    <span className="bd-breakdown-label">Transactions</span>
                    <span className="bd-breakdown-value">${transactionSpent.toFixed(2)}</span>
                </div>
                <div className="bd-breakdown-item">
                    <span className="bd-breakdown-label">Subscriptions</span>
                    <span className="bd-breakdown-value">${subscriptionSpent.toFixed(2)}</span>
                </div>
            </div>


            {/* Progress Bar */}
            <div className="budget-progress-section">
                <div className="progress-bar">
                    <div
                        className={`progress-fill ${isOver ? 'over' : ''}`}
                        style={{ width: `${Math.min(percentUsed, 100)}%`}}
                    />
                </div>
            </div>

            {/* Period Info */}
            {(budget.period_start || budget.period_end) && (
                <div className="budget-period-info">
                    <span className="period-label">Period</span>
                    <span className="period-value">
                        {budget.period_start || 'N/A'} - {budget.period_end || 'N/A'}
                    </span>
                </div>
            )}

            {/* Transactions List */}
            <div className="budget-transactions">
                <h4>Transactions ({transactions.length})</h4>

                {transactions.length === 0 ? (
                    <p className="no-transactions">No transactions for this budget.</p>
                ) : (
                    <div className="bd-transactions-table-wrapper">
                        <table className="bd-transactions-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Description</th>
                                    <th>Amount</th>
                                </tr>
                            </thead>
                            <tbody>
                                {transactions.map((tx, index) => (
                                    <tr key={tx.id || index}>
                                        <td>{tx.date || 'N/A'}</td>
                                        <td>{tx.description || '-'}</td>
                                        <td>${parseAmount(tx.amount).toFixed(2)}</td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot>
                                <tr>
                                    <td colSpan="2" className="total-label">Total</td>
                                    <td className="total-value">${spent.toFixed(2)}</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                )};
            </div>
            
            {/* Subscriptions Section */}
            {subscriptions.length > 0 && (
                <div className="budget-subscriptions">
                    <h4>Subscriptions ({subscriptions.length})</h4>
                    <div className="bd-subscriptions-list">
                        {subscriptions.map((sub, index) => (
                            <div key={sub.id || index} className="bd-subscription-item">
                                <div className="bd-sub-info">
                                    <span className="bd-sub-name">{sub.name}</span>
                                    <span className="bd-sub-cycle">{sub.billing_cycle}</span>
                                </div>
                                <span className="bd-sub-amount">${parseAmount(sub.amount).toFixed(2)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Budget;
