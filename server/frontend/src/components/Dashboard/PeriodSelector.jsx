import './PeriodSelector.css'

const PeriodSelector = ({ periods, selected, onSelect }) => {
    return (
        <div className="dashboard-period-selector">
            {periods.map((period) => (
                <button
                    key={period}
                    className={`period-btn ${selected === period ? "active" : ""}`}
                    onClick={() => onSelect(period)}
                >
                    {period.charAt(0).toUpperCase() + period.slice(1)}
                </button>
            ))}
        </div>
    );
};

export default PeriodSelector;