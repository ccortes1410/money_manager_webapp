import { useMemo } from "react";
import { Doughnut } from "react-chartjs-2";

const BudgetsCard = ({ budgets, period }) => {
    const {
        total_budgeted = 0,
        total_spent = 0,
        remaining = 0,
        percent_used = 0
    } = budgets;

    const isOverBudget = remaining < 0;
    const displayRemaining = Math.max(remaining, 0);
    const displayOverage = Math.abs(Math.min(remaining, 0));

    const COLORS = {
        spent: isOverBudget ? 'rgba(239, 68, 68, 1)' : 'rgba(59, 130, 246, 1)',
        remaining: 'rgba(34, 197, 94, 1)',
        overage: 'rgba(239, 68, 68, 1)',
    };

    const chartData = useMemo(() => {
        if (isOverBudget) {
            return {
                labels: ['Spent', 'Remaining'],
                datasets: [{
                    data: [total_budgeted, displayRemaining],
                    backgroundColor: [COLORS.spent, COLORS.overage],
                    borderWidth: 0,
                }],
            };
        }
        return {
            labels: ['Spent', 'Remaining'],
            datasets: [{
                data: [total_spent, displayRemaining],
                backgroundColor: [COLORS.spent, COLORS.remaining],
                borderWidth: 0,
            }],
        };
    }, [total_spent, displayRemaining, isOverBudget, displayOverage, total_budgeted])

    const chartOptions = useMemo(() => ({
        responsive: true,
        maintainAspectRatio: false,
        cutout: "70%",
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                callbacks: {
                    label: (context) => {
                        const value = context.raw;
                        const percent = total_budgeted > 0
                            ? ((value / total_budgeted) * 100).toFixed(1)
                            : 0;
                        return `$${value.toFixed(0)} (${percent}%)`;
                    },
                },
            },
        },
    }), [total_budgeted]);

    const centerTextPlugin = useMemo (() => ({
        id: "centerTextBudget",
        afterDraw(chart) {
            const meta = chart.getDatasetMeta(0);
            if (!meta?.data?.length) return;

            const { ctx } = chart;
            const centerX = meta.data[0].x;
            const centerY = meta.data[0].y;

            ctx.save();
            ctx.font = "bold 20px sans-serif";
            ctx.fillStyle = isOverBudget ? "#ef4444" : "#fff";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(`${Math.round(percent_used)}%`, centerX, centerY - 5);


            ctx.font = "11px sans-serif";
            ctx.fillStyle = "#888";
            ctx.fillText("Used", centerX, centerY + 15);
            ctx.restore();
        },
    }), [percent_used, isOverBudget]);

    if (total_budgeted === 0) {
        return (
            <div className="card-inner>">
                <h3>Budgets ({period})</h3>
                <div className="no-data-container">
                    <p className="no-data">No budgets for this period.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="card-inner">
            <h3>Budgets ({period})</h3>
            <div className="chart-with-legend">
                <div className="chart-container">
                    <Doughnut
                    key={`budget-${total_spent}-${total_budgeted}`}
                    data={chartData}
                    options={chartOptions}
                    plugins={[centerTextPlugin]}
                />
                </div>
                <div className="custom-legend">
                    <div className="legend-item">
                        <span
                            className="legend-color"
                            style={{ backgroundColor: isOverBudget ? COLORS.overage : COLORS.remaining}}
                        ></span>
                        <div className="legend-text">
                            <span className="legend-label">{isOverBudget ? 'Over': 'Remaining'}</span>
                            <span className={`legend-value ${isOverBudget ? 'over' : 'under'}`}>
                                ${Math.abs(remaining).toFixed(0)}
                            </span>
                        </div>
                    </div>
                    <div className="legend-item total">
                        <div className="legend-text">
                            <span className="legend-label">Budget</span>
                            <span className="legend-value">${total_budgeted.toFixed(0)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BudgetsCard;