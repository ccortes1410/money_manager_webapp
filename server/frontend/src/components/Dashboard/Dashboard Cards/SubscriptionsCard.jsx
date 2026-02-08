import { useMemo } from "react";
import { Doughnut } from "react-chartjs-2";

const SubscriptionsCard = ({ subscriptions, period }) => {
    const active = subscriptions?.active || { count: 0, total: 0};
    const inactive = subscriptions?.inactive || { count: 0, total: 0};
    const totalCount = (active.count || 0) + (inactive.count || 0);
    const totalAmount = (active.total || 0) + (inactive.total || 0);

    const COLORS = {
        active: 'rgba(34, 197, 94, 1)',
        inactive: 'rgba(107, 114, 128, 1)',
    };

    const chartData = useMemo(() => ({
        labels: ['Active','Inactive'],
        datasets: [
            {
                data: [active.count || 0, inactive.count || 0],
                backgroundColor: [COLORS.active, COLORS.inactive],
                borderWidth: 0,
                hoverOffset: 4,
            },
        ],
    }), [active.count, inactive.count]);

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
                        const label = context.label;
                        const value = context.raw;
                        const amount = label === 'Active' ? active.total : inactive.total;
                        return [`${value} subscriptions`, `$${(amount || 0).toFixed(2)}/mo`];
                    },
                },
            },
        },
    }), [active.total, inactive.total]);

    const centerTextPlugin = useMemo(() => ({
        id: "centerTextSubs",
        afterDraw(chart) {
            const meta = chart.getDatasetMeta(0);
            if (!meta?.data?.length) return;

            const { ctx } = chart;
            const centerX = meta.data[0].x;
            const centerY = meta.data[0].y;

            ctx.save();
            ctx.font = "bold 24px sans-serif";
            ctx.fillStyle = "#fff";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(totalCount, centerX, centerY - 5);

            ctx.font = "11px sans-serif";
            ctx.fillStyle = "#888";
            ctx.fillText("Subscriptions", centerX, centerY + 15);
            ctx.restore();
        }
    }), [totalCount]);

    if (totalCount === 0) {
        return (
            <div className="card-inner">
                <h3>Subscriptions ({period})</h3>
                <div className="no-data-container">
                    <p className="no-data">No subscriptions for this period.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="card-inner">
            <h3>Subscriptions ({period})</h3>
            <div className="chart-with-legend">
                <div className="chart-container">
                    <Doughnut
                        key={`subs-${totalCount}-${totalAmount}`}
                        data={chartData}
                        options={chartOptions}
                        plugins={[centerTextPlugin]}
                    />
                </div>
                <div className="custom-legend">
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: COLORS.active }}></span>
                        <div className="legend-text">
                            <span className="legend-label">Active</span>
                            <span className="legend-value">{active.count} · ${(active.total || 0).toFixed(0)}/mo</span>
                        </div>
                    </div>
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: COLORS.inactive }}></span>
                        <div className="legend-text">
                            <span className="legend-label">Inactive</span>
                            <span className="legend-value">{inactive.count} · ${(inactive.total || 0).toFixed(0)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>



        //     <div className="subscriptions-summary">
        //         <div className="sub-stat active">
        //             <h4>Active</h4>
        //             <p className="count">{active?.count || 0}</p>
        //             <p className="amount">${(active?.total || 0).toFixed(0)}</p>
        //         </div>

        //         <div className="sub-state inactive">
        //             <h4>Inactive</h4>
        //             <p className="count">{inactive?.count || 0}</p>
        //             <p className="amount">${(inactive?.total || 0).toFixed(0)}</p>
        //         </div>
        //     </div>

        //     {active?.items?.length > 0 && (
        //         <ul className="subscription-list">
        //             {active.items.map((sub) => (
        //                 <li key={sub.id}>
        //                     <span>{sub.name}</span>
        //                     <span>${sub.amount}</span>
        //                 </li>
        //             ))}
        //         </ul>
        //     )}
        // </div>
    );
};

export default SubscriptionsCard;