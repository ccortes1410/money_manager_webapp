import { Doughnut } from "react-chartjs-2";
import { useMemo } from 'react';

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

const CategorySpendingCard = ({ categories = {}, period }) => {
    const categoryList = categories?.categories || [];
    const grandTotal = categories?.total || 0;
    const transactionTotal = categories?.transaction_total || 0;
    const subscriptionTotal = categories?.subscription_total || 0;
    
    // Move the early return BEFORE useMemo hooks that depend on categoryList
    const hasValidData = Array.isArray(categoryList) && categoryList.length > 0;
    console.log("valid?", hasValidData)
    const chartData = useMemo(() => {
        
        if (!hasValidData) {
            return {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [],
                    borderWidth: 0,
                    hoverOffset: 4,
                }],
            };
        }

        return {
            labels: categoryList.map((c) => c.category),
            datasets: [
                {
                    data: categoryList.map((c) => c.total),
                    backgroundColor: COLORS.slice(0, categoryList.length),
                    borderWidth: 0,
                    hoverOffset: 4,
                },
            ],
        };
    }, [categoryList, hasValidData]);

    console.log("Categories recevied:", categories)

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
                        const category = categoryList[context.dataIndex];
                        const percent = grandTotal > 0
                            ? ((category.total / grandTotal) * 100).toFixed(1)
                            : 0;
                        return `$${category.total.toFixed(0)} (${percent}%)`;
                    },
                },
            },
        },
    }), [categoryList, grandTotal]);

    const centerTextPlugin = useMemo(() => ({
        id: "centerTextCategory",
        afterDraw(chart) {
            const meta = chart.getDatasetMeta(0);
            if (!meta?.data?.length) return;

            const { ctx } = chart;
            const centerX = meta.data[0].x;
            const centerY = meta.data[0].y;

            ctx.save();
            ctx.font = "bold 18px sans-serif";
            ctx.fillStyle = "#fff";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(`$${grandTotal.toLocaleString()}`, centerX, centerY - 5);

            ctx.font = "11px sans-serif";
            ctx.fillStyle = "#888";
            ctx.fillText("Total Spent", centerX, centerY + 15);
            ctx.restore();
        },
    }), [grandTotal]);

    if (!categoryList.length) {
        return (
            <div className="card-inner">
                <h3>Categories ({period})</h3>
                <div className="no-data-container">
                    <p>No spending data for this period</p>
                </div>
            </div>
        );
    }

    const topCategories = categoryList.slice(0, 5);
    const otherCategories = categoryList.slice(5);
    const otherTotal = otherCategories.reduce((sum, c) => sum + c.total, 0);

    return (
        <div className="card-inner">
            <h3>Categories ({period})</h3>
            <div className="chart-with-legend">
                <div className="chart-container">
                    <Doughnut
                        key={`category-${grandTotal}-${categoryList.length}`}
                        data={chartData}
                        options={chartOptions}
                        plugins={[centerTextPlugin]}    
                    />
                </div>

                <div className="custom-legend scrollable">
                    {topCategories.map((cat, index) => {
                        const percent = grandTotal > 0
                            ? ((cat.total / grandTotal) * 100).toFixed(0)
                            : 0;
                        return (
                            <div key={cat.category} className="legend-item">
                                <span
                                    className="legend-color"
                                    style={{ backgroundColor: COLORS[index] }}
                                />
                                <div className="legend-text">
                                    <span className="legend-label">{cat.category}</span>
                                    <span className="legend-value">
                                        ${cat.total.toFixed(0)} · {percent}%
                                    </span>
                                </div>
                            </div>
                        );
                    })}

                    {otherCategories.length > 0 && (
                        <div className="legend-item">
                            <span
                                className="legend-color"
                                style={{ backgroundColor: '#666'}}
                            />
                            <div className="legend-text">
                                <span className="legend-label">Other ({otherCategories.length})</span>
                                <span className="legend-value">${otherTotal.toFixed(0)}</span>
                            </div>
                        </div>
                    )}

                    {/* Summary row */}
                    <div className="legend-item summary">
                        <div className="legend-text">
                            <div className="summary-row">
                                <span className="summary-label">Transactions</span>
                                <span className="summary-value">${transactionTotal.toFixed(0)}</span>
                            </div>
                            <div className="summary-row">
                                <span className="summary-label">Subscriptions</span>
                                <span className="summary-value">${subscriptionTotal.toFixed(0)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CategorySpendingCard;