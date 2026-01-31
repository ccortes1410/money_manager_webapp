import { Pie } from "react-chartjs-2";
import { useMemo } from 'react';

const CategorySpendingCard = ({ categories = {}, period }) => {
    const categoryList = categories?.categories || [];
    const grandTotal = categories?.total || 0;

    const COLORS = [
        'rgba(75,192,192,1)',
        'rgba(153,102,255,1)',
        'rgba(255,159,64,1)',
        'rgba(255,99,132,1)',
        'rgba(54,162,235,1)',
        'rgba(255,206,86,1)',
        'rgba(243, 0, 41, 1)',
        'rgba(62, 219, 75, 1)',
        'rgba(200, 91, 233, 1)',
    ];

    const getPieChartData = () => {
        if (!Array.isArray(categoryList) || categoryList.length === 0) {
            return null;
        }

        return {
            labels: categoryList.map((c) => c.category),
            datasets: [
                {
                    data: categoryList.map((c) => c.total),
                    backgroundColor: COLORS.slice(0, categoryList.length),
                    borderWidth: 1,
                }
            ]
        }
    }

    const pieData = getPieChartData();

    const chartData = {
        labels: categories.categories.map((c) => c.category),
        datasets: [
            {
                data: categories.categories.map((c) => c.total),
                backgroundColor: COLORS.slice(0, categories.categories.length),
                borderWidth: 1
            },
        ],
    };

    const donutOptions = {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "70%",
        plugins: {
            legend: {
                position: "bottom",
                labels: {
                    color: "#110101",
                    boxWidth: 12,
                    padding: 16,
                },
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const value = context.raw;
                        const percent = ((value / categories.total) * 100).toFixed(1);
                        return `$${value} (${percent}%)`;
                    },
                },
            },
        },
    };
    console.log("Categories recevied:", categories)
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
        legend: {
            position: "right",
            labels: {
            color: "#fff",
            padding: 12,
            usePointStyle: true,
            },
        },
        tooltip: {
            callbacks: {
            label: (context) => {
                const category = categoryList[context.dataIndex];
                const lines = [`Total: $${category.total.toFixed(2)}`];
                
                if (category.transactions > 0) {
                lines.push(`Transactions: $${category.transactions.toFixed(2)}`);
                }
                if (category.subscriptions > 0) {
                lines.push(`Subscriptions: $${category.subscriptions.toFixed(2)}`);
                }
                lines.push(`${category.percentage}%`);
                
                return lines;
            },
            },
        },
        },
    };

    const centerTextPlugin = useMemo(() => ({
        id: "centerText",
        afterDraw(chart) {
            const meta = chart.getDatasetMeta(0);
            if (!meta || !meta.data || meta.data.length === 0) {
                return; // No data, don't draw center text
            }

            const { ctx } = chart;
            const centerX = chart.getDatasetMeta(0).data[0].x;
            const centerY = chart.getDatasetMeta(0).data[0].y;

            // const total = categories?.total || 0;
            const formattedTotal = grandTotal.toLocaleString();

            ctx.save();
            ctx.font = "bold 18px sans-serif";
            ctx.fillStyle = "#080202";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(`$${formattedTotal}`, centerX, centerY - 5);

            ctx.font = "12px sans-serif";
            ctx.fillStyle = "#ccc";
            ctx.fillText("Total Spent", centerX, centerY + 15);
            ctx.restore();
        },
    }), [grandTotal]);

    

    if (!categoryList.length) {
        return (
            <div className="dashboard-card categories">
                <h3>Category Spending ({period})</h3>
                <p>No spending data for this period</p>
            </div>
        );
    }

    return (
        <div className="dashboard-card categories">
            <h3>Category Spending ({period})</h3>
            <Pie data={pieData} options={donutOptions} plugins={[centerTextPlugin]}/>
            {/* <ul className="category-list">
                {categories.categories.map((c) => (
                    <li key={c.category}>
                        <span>{c.category}</span>
                        <span>${c.total.toFixed(0)} ({c.percentage}%)</span>
                    </li>
                ))}
            </ul> */}
        </div>
    );
};

export default CategorySpendingCard;