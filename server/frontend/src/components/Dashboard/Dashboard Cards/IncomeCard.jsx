
import { Bar } from "react-chartjs-2";

const IncomeCard = ({ income, period }) => {
    const {
        total_income = 0,
        total_spent = 0,
        remaining = 0,
        percent_remaining = 0,
        is_negative = false
    } = income;

    const spentPercent = total_income > 0
        ? Math.min((total_spent / total_income) * 100, 100)
        : 0;

    return (
        <div className="card income-card">
            <h3>Remaining Income ({period})</h3>

            {/* Summary numbers*/}
            <div className="income-summary">
                <div className="income-stat">
                    <span className="label">Income</span>
                    <span className="value">${total_income.toFixed(0)}</span>
                </div>
                <div className="income-stat">
                    <span className="label">Spent</span>
                    <span className="value">${remaining.toFixed(0)}</span>
                </div>
                <div className={`income-stat remaining ${is_negative ? "negative" : "positive"}`}>
                    <span className="label">Remaining</span>
                    <span className="value">${remaining.toFixed(0)}</span>
                </div>
            </div>

            {/*Single bar visualization*/}
            <div className="income-bar-container">
                <div className="income-bar-background">
                    <div
                        className={`income-bar-fill ${is_negative ? "over" : ""}`}
                        style={{ height: `${spentPercent}%`}}
                    />
                </div>
                <div className="income-bar-labels">
                    <span>${remaining.toFixed(0)}</span>
                </div>
            </div>
        </div>
    );
};

export default IncomeCard;