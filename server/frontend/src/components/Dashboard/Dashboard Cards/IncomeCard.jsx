
const IncomeCard = ({ income, period }) => {
    const {
        total_income = 0,
        total_spent = 0,
        remaining = 0,
    } = income;

    const isNegative = remaining < 0;

    // Calculate fill percentage (remaining funds as % of income)
    const fillPercent = total_income > 0
        ? Math.max(0, Math.min(100, (remaining / total_income) * 100))
        : 0;

    // Calculate spent percentage for the bar
    const spentPercent = total_income > 0
        ? Math.min(100, (total_spent / total_income) * 100)
        : 0;

    if (total_income === 0) {
        return (
            <div className="card-inner">
                <h3>Income ({period})</h3>
                <div className="no-ta-container">
                    <p className="no-data">No income for this period.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="card-inner">
            <h3>Income ({period})</h3>
            <div className="dashboard-income-content">
                {/* Top label - Remaining */}
                <div className="dashboard-income-label top">
                    <span className={`amount ${isNegative ? 'negative' : 'positive'}`}>
                        {isNegative ? '-' : ''}${Math.abs(remaining).toFixed(0)}
                    </span>
                    <span className="label">{isNegative ? 'Over Budget' : 'Remaining'}</span>
                </div>

                {/*  Vertical Bar */}
                <div className="dashboard-income-bar-container">
                    <div className="dashboard-income-bar">
                        {/* Remaining funs (green) - fills from bottom */}
                        <div
                            className={`dashboard-income-bar-fill remaining ${isNegative ? 'negative' : ''}`}
                            style={{ height: `${isNegative ? 0 : fillPercent}%`}}
                        />
                        {/* Spent funds (blue) - fills from bottom above remaining */}
                        <div 
                            className="dashboard-income-bar-fill spent"
                            style={{ height: `${Math.min(spentPercent, 100)}%`}}
                        />
                        {/* Overage (red) - shows when over budget */}
                        {isNegative && (
                            <div
                                className="dashboard-income-bar-fill overage"
                                style={{ height: `${Math.min(Math.abs((remaining / total_income) * 100), 30)}%` }}
                            />
                        )}
                    </div>

                    {/* Scale markers */}
                    <div className="dashboard-income-bar-scale">
                        <span>100%</span>
                        <span>50%</span>
                        <span>0%</span>
                    </div>
                </div>

                {/* Bottom labels */}
                <div className="dashboard-income-stats">
                    <div className="dashboard-income-stat">
                        <span className="dashboard-stat-color income"></span>
                        <div className="dashboard-stat-text">
                            <span className="dashboard-stat-label">Income</span>
                            <span className="dashboard-stat-value">${total_income.toFixed(0)}</span>
                        </div>
                    </div>
                    <div className="dashboard-income-stat">
                        <span className="dashboard-stat-color spent"></span>
                        <div className="dashboard-stat-text">
                            <span className="dashboard-stat-label">Spent</span>
                            <span className="dashboard-stat-value">${total_spent.toFixed(0)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default IncomeCard;