import React, { useContext, useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import './Dashboard.css';
import '../assets/style.css';
import { Line, Pie, Bar } from 'react-chartjs-2';
import { BarElement, ArcElement, Chart, LineController, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Title} from 'chart.js';

Chart.register(BarElement, ArcElement, LineController, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Title);

const Dashboard = () => {
    // const [collapsed, setCollapsed] = useState(true);
    const { user } = useContext(AuthContext);
    const [subscriptions, setSubscriptions] = useState([]);
    const [budgets, setBudgets] = useState([]);
    const [transactions, setTransactions] = useState([]);
    const [allData, setAllData] = useState([]);
    const [data, setData] = useState([]);
    
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
    let trans_url = "/djangoapp/transactions";
    let subs_url = "/djangoapp/subscriptions";
    let budget_url = "/djangoapp/budgets";

    const navigate = useNavigate();

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
            if (retobj.budgets) {
                let budgets = Array.from(retobj.budgets)
                .filter(bud => bud.user_id === user.id);
                setBudgets(budgets);
            } else {
                setBudgets([]);
            }
        } catch (error) {
            console.error("Error fetching budgets: ", error);
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
    
    const pieChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: true },
            // title: { display: true, text: 'Spending by Category' },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let label = context.label || '';
                        let value = context.raw || 0;
                        return `$${value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                    }
                },
                intersect: true,
                mode: "nearest",
                enables: true,
            },   
        },
        size: {
            height: '250px',
            width: '250px',
        }
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

    const handleAddTransaction = async() => {
        const amount = amountInput;
        const date = dateInput || getToday();
        const description = descriptionInput;
        const category = categoryInput || "General";

        // Add validation if needed

        const newTransaction = {
            amount: parseFloat(amount),
            date: date,
            description: description,
            category: category
        };

        try {
            const response = await fetch(trans_url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(newTransaction)
            });
            const result = await response.json();
            if (response.status === 201 || result.status === 201) {
                get_transactions();
                setAmountInput('');
                setDateInput('');
                setDescriptionInput('');
                setCategoryInput('');
            } else {
                alert("Error adding transaction");
            }
        } catch (error) {
            alert("Failed to add transaction.");
            console.error(error);
        }
    }
    
    const handleCheckboxChange =(id) => {
        setSelectedTransactions(prev => 
            prev.includes(id) ?
            prev.filter(tid => tid !== id) :
            [...prev, id]
        );
    };

    const handleDeleteTransaction = async () => {
        if (selectedTransactions.length === 0) return;
        try {
            const response = await fetch(trans_url, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ ids: selectedTransactions })
            });
            if (response.status === 200) {
                get_transactions();
                setSelectedTransactions([]);
            } else {
                alert("Failed to delete transactions");
            }
        } catch (error) {
            alert("Error deleting transactions");
            console.error(error);
        }
    }

    const handleInputChange = (e) => {
        const query = e.target.value;
        setSearchQuery(query);

        const filtered = allData.filter((transaction) =>
            transaction.description.toLowerCase().includes(query.toLowerCase())
        );
        if (filtered.length > 0 || query === "") {
            setData(filtered.length > 0 ? filtered : allData);
        }
    }
    
    const handleLostFocus = () => {
        if (!searchQuery) {
            setData(allData);
        }
    }
    
    useEffect(() => {
        get_transactions();
        get_subscriptions();
        get_budgets();
    }, []);

    // useEffect(() => {
    //     if (data.length > 0) {
    //         console.log("Sample transaction:", data[0]);
    //     }
    // }, [data]);

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

    return (
            <div className='main-section'>
                <div className="dashboard-header">
                    <h1 style={{ color: '#fff' }}>Dashboard</h1>
                    <div className="active-user">
                            <p style={{ marginTop: '10px' }}>{user ? user.username : "Not Logged In"}</p>
                    </div>
                </div>
                <div 
                    className="dashboard-container"
                    style={{
                        transition: "margin-left 0.2s"
                    }}>
                    <div className="dashboard-card transactions">
                        <h4 style={{ textAlign: 'center' }}>Transaction Overview</h4>
                        <div className="chart-wrapper line-chart-wrapper">
                             {getMonthlySpending && getMonthlySpending.labels && getMonthlySpending.labels.length > 0 ? ( 
                            <>
                            <div>
                                <label>
                                    Select Year: {' '}
                                    <select
                                        value={selectedYear}
                                        onChange={(e) => setSelectedYear(Number(e.target.value))}
                                        >
                                            {years.map((y) => (
                                                <option key={y} value={y}>
                                                    {y}
                                                </option>
                                            ))}
                                        </select>
                                </label>
                             </div>
                            <Bar data={getMonthlySpending} options={monthlySpendingOptions}/>
                          </>
                        ) : (
                            <p style={{ textAlign: 'center' }}>No data available</p>
                        )}
                        </div>
                    </div>
                    <div className="dashboard-card categories">
                        <h4 style={{ textAlign: 'center' }}>Spending by Category</h4>
                        <div className="chart-wrapper pie-chart-wrapper">
                            {pieChartData && pieChartData.labels && pieChartData.labels.length > 0 ? (
                                <Pie data={pieChartData} options={pieChartOptions} />
                            ) : (
                                <p style={{ textAlign: 'center' }}>No data available</p>
                            )}
                        </div>
                    </div>
                    <div className="dashboard-card subscriptions">
                        <h2 style={{ textAlign: 'center' }}>Subscriptions Total</h2>
                        {subscriptions && subscriptions.length > 0 ? (
                            <div className="subscription-wrapper">
                                <h4>Active Subscriptions</h4>
                                <p style={{ fontSize: '20px', textAlign: 'center' }}>${activeSubs.reduce((acc, item) => acc + Number(item.amount), 0)}</p>

                                <h4> Inactive Subcriptions</h4>
                                <p style={{ fontSize: '20px', textAlign: 'center' }}>${inactiveSubs.reduce((acc, item) => acc + Number(item.amount), 0)}</p>
                            </div>
                        ) : (
                            <p>No Data Available</p>
                        )}
                    </div>
                    <div className="dashboard-card budgets">
                        <h4 style={{ textAlign: 'center' }}>Budget Total</h4>
                        {budgets && budgets.length > 0 ? (
                            <div className="budget-wrapper">
                                <p style={{ fontSize: '36px', textAlign: 'center' }}>${budgets.reduce((acc, item) => acc + Number(item.amount), 0)}</p>
                            </div>
                        ) : (
                            <p>No Data Available</p>
                        )}
                    </div>
            </div>
        </div>
    )
}
export default Dashboard;