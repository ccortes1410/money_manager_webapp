import React, { useContext, useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import './Dashboard.css';
import '../assets/style.css';
import { BarElement, ArcElement, Chart, LineController, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Title} from 'chart.js';
import PeriodSelector from './PeriodSelector';
import TransactionsCard from './Dashboard Cards/TransactionsCard';
import CategorySpendingCard from './Dashboard Cards/CategorySpendingCard';
import SubscriptionsCard from './Dashboard Cards/SubscriptionsCard';
import BudgetsCard from './Dashboard Cards/BudgetsCard';
import IncomeCard from './Dashboard Cards/IncomeCard';
Chart.register(BarElement, ArcElement, LineController, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Title);

const PERIODS = ["daily", "weekly", "monthly", "yearly", "total"];

const Dashboard = () => {
    // const [collapsed, setCollapsed] = useState(true);
    const { user } = useContext(AuthContext);
    const [ dashboard, setDashboard ] = useState({
        transactions: [],
        categories: {
            categories: [],
            total: 0,
            transaction_total: 0,
            subscription_total: 0
        },
        subscriptions: [],
        budgets: [],
        income: {
        total: 0,
        by_source: []
        },
        period: {
        value: "monthly",
        label: "Last 30 Days"
        }
    });
    const [subscriptions, setSubscriptions] = useState([]);
    const [budgets, setBudgets] = useState([]);
    const [transactions, setTransactions] = useState([]);
    const [income, setIncome] = useState([]);
    const [allData, setAllData] = useState([]);
    const [data, setData] = useState([]);
    
    const [error, setError] = useState(null);
    const [ loading, setLoading ] = useState(true);
    const [ selectedPeriod, setSelectedPeriod ] = useState("monthly");
    const [searchQuery, setSearchQuery] = useState("");
    const [amountInput, setAmountInput] = useState('');
    const [dateInput, setDateInput] = useState('');
    const [categoryInput, setCategoryInput] = useState('');
    const [descriptionInput, setDescriptionInput] = useState('');
    const [selectedTransactions, setSelectedTransactions] = useState([]);

    // Set an array for years to display on bar graph
    const years = Array.from(
        new Set(transactions.map((t) => new Date(t.date).getFullYear()))
    ).sort((a, b) => b - a);

    const currentYear = new Date().getFullYear();
    const [selectedYear, setSelectedYear] = useState(currentYear);

    const getToday = () => {
        const today = new Date();
        return today.toISOString().split('T')[0];
    };

    // Set the urls from where to get data
    let dashboard_url = "/djangoapp/dashboard";

    let trans_url = "/djangoapp/transactions";
    let subs_url = "/djangoapp/subscriptions";
    let budget_url = "/djangoapp/budgets";
    let income_url = "/djangoapp/income";
    

    const navigate = useNavigate();
    useEffect(() => {
        const get_dashboard = async () => {
            setLoading(true);
            setError(null);

            try {
                const res = await fetch(dashboard_url+`?period=${selectedPeriod}`, {
                    method: 'GET',
                    credentials: 'include'
                });
                
                if (!res.ok) throw new Error("Failed to fetch dashboard");

                const data = await res.json();
                setDashboard(data.dashboard)
            } catch (error) {
                console.log("Couldn't fetch dashboard:", error)
                setError("Failed to load dashboard data");
            } finally {
                setLoading(false);
            }
        }
        get_dashboard();
    }, [selectedPeriod])
    


    const get_transactions = async () => {
        try {
            const res = await fetch(trans_url, {
            method: 'GET',
            credentials: 'include',
            });

            const retobj = await res.json();
            if (retobj.transactions) {
                let transactions = Array.from(retobj.transactions)
                .filter(tx => tx.user_id === user.id);
                setTransactions(transactions);
                setData(transactions);
            } else {
                setTransactions([]);
                setData([]);
            }
        } catch (error) {
            console.error("Error fetching transactions:", error);
        }
        
    }

    const get_subscriptions = async () => {
        try {
            const res = await fetch(subs_url, {
                method: 'GET',
                credentials: 'include',
            });

            const retobj = await res.json();
            if (retobj.subscriptions) {
                let subscriptions = Array.from(retobj.subscriptions)
                .filter(sub => sub.user_id === user.id);
                setSubscriptions(subscriptions);
            } else {
                setSubscriptions([]);
            }
        } catch (error) {
            console.error("Error fetching subscriptions: ", error);
        }
    }

    const get_budgets = async () => {
        try {
            const res = await fetch(budget_url, {
                method: 'GET',
                credentials: 'include',
            });

            const retobj = await res.json();
            if (res.ok) {
                setBudgets(retobj.budgets);
            } else {
                setBudgets([]);
            }
        } catch (error) {
            console.error("Error fetching budgets: ", error);
        }
    }
    
    const get_income = async () => {
        try {
            const res = await fetch(income_url, {
                method: 'GET',
                credentials: 'include',
            });

            const retobj = await res.json();
            console.log(retobj)
            if (retobj.incomes) {
                let income = Array.from(retobj.incomes)
                .filter(inc => inc.user_id === user.id);
                setIncome(income);
            } else {
                setIncome([]);
                console.log("Couldn't fetch income")
            }
        } catch (error) {
            console.error("Error fetching income: ", error);
        }
    }

    const monthlySpending = useMemo(() => {
        const totals = Array(12).fill(0);

        transactions.forEach((t) => {
            const date = new Date(t.date);
            if (date.getFullYear() === selectedYear) {
                const m = date.getMonth();
                totals[m] += Number(t.amount);
            }
        });
    // console.log(date);
        return totals;
    }, [transactions, selectedYear]);

    const monthLabels = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ];


    const monthlySpendingOptions = {
        responsive: true,
        plugins: {
            legend: { display: false },
            title: { display: true, text: `${selectedYear}` },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let label = context.label || '';
                        let value = context.raw || 0;
                        return `$${value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                    }
                }
            }
        },
        scales: {
            y: { beginAtZero: true, title: { display: true, text: "Amount ($)" } },
            x: { title: { display: true } },
        },
    };

    const getMonthlySpending = {
        labels: monthLabels,
        datasets: [
            {
                label: "Spending per Month",
                data: monthlySpending,
                backgroundColor: "#dc3545",
                borderRadius: 4,
                barThickness: 20,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: { display: true },
            // title: { display: true, text: 'Transaction Overview' },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let label = context.label || '';
                        let value = context.raw || 0;
                        return `$${value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                    }
                }
            }
        },
        scales: {
            x: { title: {display: true, text: 'Date'} },
            y: { title: { display: true, text: 'Amount'} }
        },
        size: {
            height: '250px',
            width: '250px',
        }
    };

    const getChartData = () => {
        if (!Array.isArray(transactions) || transactions.length === 0) return null;

        const dateMap = {};
        transactions.forEach(tx => {
            if (tx.date && tx.amount && !isNaN(Number(tx.amount))) {
                if(!dateMap[tx.date]) {
                    dateMap[tx.date] = 0;
                }
                dateMap[tx.date] += Number(tx.amount);
            }
        });

        const dates = Object.keys(dateMap).sort();
        const amounts = dates.map(date => dateMap[date]);

        if (dates.length === 0) return null;

        return {
            labels: dates,
            datasets: [
                {
                    label: 'Total Amount',
                    data: amounts,
                    fill: false,
                    borderColor: 'rgba(75,192,192,1)',
                    backgroundColor: 'rgba(75,192,192,0.2)',
                    tension: 0.2,
                }
            ]
        }
    }

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
                        const percent = ((value / totalSpent) * 100).toFixed(1);
                        return `$${value} (${percent}%)`;
                    },
                },
            },
        },
    };

    const centerTextPlugin = {
        id: "centerText",
        afterDraw(chart) {
            const { ctx } = chart;
            const centerX = chart.getDatasetMeta(0).data[0].x;
            const centerY = chart.getDatasetMeta(0).data[0].y;

            ctx.save();
            ctx.font = "bold 18px sans-serif";
            ctx.fillStyle = "#080202";
            ctx.textAlign = "center";
            ctx.fillText(`$${totalSpent}`, centerX, centerY - 5);

            ctx.font = "12px sans-serif";
            ctx.fillStyle = "#ccc";
            ctx.fillText("Total Spent", centerX, centerY + 15);
            ctx.restore();
        },
    };

    const getPieChartData = () => {
        if (!Array.isArray(transactions) || transactions.length === 0 || !Array.isArray(subscriptions) || subscriptions.length === 0 ) return null;

        const categoryMap = {};
        transactions.forEach(tx => {
            if (tx.category && tx.amount && !isNaN(Number(tx.amount))) {
                if (!categoryMap[tx.category]) {
                    categoryMap[tx.category] = 0;
                }
                categoryMap[tx.category] += Number(tx.amount);
            }
        });

        subscriptions.forEach(sb => {
            if (sb.category && sb.amount && !isNaN(Number(sb.amount))) {
                if (!categoryMap[sb.category]) {
                    categoryMap[sb.category] = 0;
                }
                categoryMap[sb.category] += Number(sb.amount);
            }
        })

        const categories = Object.keys(categoryMap);
        const amounts = categories.map(cat => categoryMap[cat]);

        if (categories.length === 0 ) return null;

        const colors = [
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

        return {
            labels: categories,
            datasets: [
                {
                    data: amounts,
                    backgroundColor: colors.slice(0, categories.length),
                    borderWidth: 1
                }
            ]
        };
    };
    
    function getCurrentMonthRange() {
        const now = new Date();

        const year = now.getUTCFullYear();
        const month = now.getUTCMonth();

        const start = new Date(year, month, 1);
        const end = new Date(year, month + 1, 0);

        return { start, end };
    }

    function overlapsMonth(periodStart, periodEnd, monthStart, monthEnd) {
        return (
            periodStart <= monthEnd &&
            periodEnd >= monthStart
        );
    }

    const { start: monthStart, end: monthEnd} = getCurrentMonthRange();
    
    const currentMonthIncome = useMemo(() => {
        return income.filter(item => {
            const start = new Date(item.period_start + "T00:00:00");
            const end = new Date(item.period_end + "T23:59:59");

            return overlapsMonth(start, end, monthStart, monthEnd);
        });
    }, [income]);

    const currentMonthSpending = useMemo(() => {
        return transactions.filter(item => {
            const start = new Date(item.date + "T00:00:00");
            const end = new Date(item.date + "T23:59:59");

            return overlapsMonth(start, end, monthStart, monthEnd);
        })
    }, [transactions]);

    const totalSpendingThisMonth = useMemo(() => {
        return currentMonthSpending.reduce(
            (sum, item) => sum + Number(item.amount),
            0
        );
    }, [currentMonthSpending])

    const totalIncomeThisMonth = useMemo(() => {
        return currentMonthIncome.reduce(
            (sum, item) => sum + Number(item.amount),
            0
        );
    }, [currentMonthIncome]);

    
    // const remainingFundsPercent = (totalSpendingThisMonth / totalIncomeThisMonth) * 100;

    const totalInc = totalIncomeThisMonth || 0;
    const spentInc = totalSpendingThisMonth || 0;

    const remainingFunds = Math.max(0, totalInc - spentInc );

    const remainingFundsPercent = totalInc > 0 ? Math.min(100, (remainingFunds / totalInc ) * 100) : 0;

    // console.log("Current month spending: ", currentMonthSpending)
    // console.log("Total Spending: ", totalSpendingThisMonth)
    // console.log("Total Income: ", totalIncomeThisMonth)
    // console.log(remainingFundsPercent)   
    
    useEffect(() => {
        get_transactions();
        get_subscriptions();
        get_budgets();
        get_income();
    }, []);


    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/login');
        }
    }, [user]);

    const chartData = getChartData();
    // console.log(chartData);

    const pieChartData = getPieChartData();
    // console.log(pieChartData);

    const activeSubs = subscriptions.filter(sub => sub.is_active)
    const inactiveSubs = subscriptions.filter(sub => !sub.is_active)

    const activeTotalSubs = activeSubs.reduce((a, s) => a + Number(s.amount), 0);
    const inactiveTotalSubs = inactiveSubs.reduce((a, s) => a + Number(s.amount), 0);
    const sumSubs = activeTotalSubs + inactiveTotalSubs;

    const totalBudget = budgets.reduce((a, b) => a + Number(b.amount), 0);
    const budgetsSpent = budgets.reduce((acc, sum) => acc + Number(sum.spent), 0);
    const budgetPercentUsed = Math.min(100, (budgetsSpent / totalBudget) * 100);

    const totalSpent = transactions.reduce((a,b) => a + Number(b.amount), 0);

    console.log("Dashboard fetched:", dashboard)
    console.log("Categories:", dashboard.categories)
    console.log("Transactions:", dashboard.transactions)


    if (error) {
        return (
        <div className="dashboard-error">
            <p>{error}</p>
            <button onClick={() => setSelectedPeriod(selectedPeriod)}>
            Retry
            </button>
        </div>
        );
    }
    
    if (loading) {
        return (
            <div className="dashboard-page">
                <div className="dashboard-header">
                    <h1>Dashboard</h1>
                </div>
                <div className="period-selector-wrapper">
                    <PeriodSelector
                        periods={PERIODS}
                        selected={selectedPeriod}
                        onSelect={setSelectedPeriod}
                    />
                </div>
                <div className="dashboard-loading">
                    <p>Loading dashboard...</p>
                </div>
            </div>
        );
    }
    return (  
        <div className="dashboard-page">
            {/* Fixed header */}
            <div className="dashboard-header">
                <h1>Dashboard</h1>
                {/* <div className="active-user">
                    <p>{user ? user.username : "Not Logged In"}</p>
                </div> */}
            </div>

            {/* Fixed period selector */}
            <div className="period-selector-wrapper">
                <PeriodSelector
                    periods={PERIODS}
                    selected={selectedPeriod}
                    onSelect={setSelectedPeriod}
                />
            </div>

            {/* Scrollable content */}
            <div className="dashboard-content">
                {/* Main cards grid */}
                <div className="dashboard-main">
                    <div className="dashboard-card transactions">
                        {console.log("TransactionsCard data:", dashboard?.transactions, "isArray:", Array.isArray(dashboard?.transactions))}
                        <TransactionsCard
                            transactions={dashboard?.transactions || []}
                            period={selectedPeriod}
                        />
                    </div>

                    <div className="dashboard-card categories">
                        {console.log("CategorySpendingCard data:", dashboard?.categories)}
                        <CategorySpendingCard
                            key={dashboard?.categories?.total}
                            categories={dashboard?.categories || {}}
                            period={selectedPeriod}
                        />
                    </div>

                    <div className="dashboard-card subscriptions">
                        {console.log("SubscriptionsCard data:", dashboard?.subscriptions, "isArray:", Array.isArray(dashboard?.subscriptions))}
                        <SubscriptionsCard
                            subscriptions={dashboard?.subscriptions}
                            period={selectedPeriod}
                        />
                    </div>

                    <div className="dashboard-card budgets">
                        {console.log("BudgetsCard data:", dashboard?.budgets, "isArray:", Array.isArray(dashboard?.budgets))}
                        <BudgetsCard
                            budgets={dashboard?.budgets}
                            period={selectedPeriod}
                        />
                    </div>
                </div>

                {/* Income sidebar */}
                <div className="dashboard-sidebar">
                    <div className="dashboard-card income">
                        {console.log("IncomeCard data:", dashboard?.income)}
                        <IncomeCard
                            income={dashboard?.income}
                            period={selectedPeriod}
                        />
                    </div>
                </div>
            </div>
        </div>
    )
}
export default Dashboard;