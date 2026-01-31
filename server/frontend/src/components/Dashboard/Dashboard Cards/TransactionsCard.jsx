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

    // const getChartData = () => {
    //     if (!Array.isArray(transactions) || transactions.length === 0) return null;

    //     const dateMap = {};
    //     transactions.forEach(tx => {
    //         if (tx.date && tx.amount && !isNaN(Number(tx.amount))) {
    //             if(!dateMap[tx.date]) {
    //                 dateMap[tx.date] = 0;
    //             }
    //             dateMap[tx.date] += Number(tx.amount);
    //         }
    //     });

    //     const dates = Object.keys(dateMap).sort();
    //     const amounts = dates.map(date => dateMap[date]);

    //     if (dates.length === 0) return null;

    //     return {
    //         labels: transactions.map((t) => t.date),
    //         datasets: [
    //             {
    //                 label: "Spending",
    //                 data: amounts,
    //                 fill: false,
    //                 borderColor: 'rgba(75,192,192,1)',
    //                 backgroundColor: 'rgba(75,192,192,0.2)',
    //                 tension: 0.2,
    //             },
    //         ],
    //     }
    // };

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
        <div className="dashboard-card transactions">
            <h3>Transactions ({period})</h3>
            <Bar data={chartData} options={chartOptions}/>
        </div>
    )
};

export default TransactionsCard;