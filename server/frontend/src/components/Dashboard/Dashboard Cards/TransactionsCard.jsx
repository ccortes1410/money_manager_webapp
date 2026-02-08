import { Bar } from "react-chartjs-2";
import './TransactionsCard.css'

const TransactionsCard = ({ transactions, period }) => {
    if (!transactions.length) {
        return (
            <div className="dashboard-card transactions">
                <h3>Transactions ({period})</h3>
                <p>No transactions for this period.</p>
            </div>
        );
    }

    const chartData = {
        labels: transactions.map((t) => t.label),
        datasets: [
            {
                label: "Spending",
                data: transactions.map((t) => t.total),
                backgroundColor: "#2f80ed",
                borderRadius: 4,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
        legend: {
            display: false,
        },
        tooltip: {
            callbacks: {
            label: (context) => `$${context.raw.toFixed(2)}`,
            },
        },
        },
        scales: {
        x: {
            grid: {
            display: false,
            },
            ticks: {
            color: "#888",
            // Show fewer labels for monthly view
            maxTicksLimit: period === "monthly" ? 10 : undefined,
            },
        },
        y: {
            grid: {
            color: "#333",
            },
            ticks: {
            color: "#888",
            callback: (value) => `$${value}`,
            },
        },
        },
    };
    // };

    // const chartData = getChartData();

    return (
        <div className="card-inner">
            <h3>Transactions ({period})</h3>
            <div className="chart-container">
                <Bar data={chartData} options={chartOptions}/>
            </div>
        </div>
    )
};

export default TransactionsCard;