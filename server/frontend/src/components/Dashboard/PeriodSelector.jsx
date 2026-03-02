import './PeriodSelector.css'
import { useTranslation } from 'react-i18next';

const PeriodSelector = ({ periods, selected, onSelect }) => {
    const  { t } = useTranslation();
    
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