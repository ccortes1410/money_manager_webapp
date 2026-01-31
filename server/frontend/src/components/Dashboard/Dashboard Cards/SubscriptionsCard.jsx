
const SubscriptionsCard = ({ subscriptions, period }) => {
    const { active, inactive, total_count } = subscriptions;

    return (
        <div className="card">
            <h3>Subscriptions ({period})</h3>

            <div className="subscriptions-summary">
                <div className="sub-stat active">
                    <h4>Active</h4>
                    <p className="count">{active?.count || 0}</p>
                    <p className="amount">${(active?.total || 0).toFixed(0)}</p>
                </div>

                <div className="sub-state inactive">
                    <h4>Inactive</h4>
                    <p className="count">{inactive?.count || 0}</p>
                    <p className="amount">${(inactive?.total || 0).toFixed(0)}</p>
                </div>
            </div>

            {active?.items?.length > 0 && (
                <ul className="subscription-list">
                    {active.items.map((sub) => (
                        <li key={sub.id}>
                            <span>{sub.name}</span>
                            <span>${sub.amount}</span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default SubscriptionsCard;