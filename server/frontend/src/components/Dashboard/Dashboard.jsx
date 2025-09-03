import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';
import '../assets/style.css';
import Sidebar from '../Sidebar/Sidebar';
import { Line } from 'react-chartjs-2';
import { Chart, LineController, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Title} from 'chart.js';

Chart.register(LineController, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Title);

const Dashboard = () => {
    const [collapsed, setCollapsed] = useState(true);
    const [user, setUser] = useState(null);
    const [allData, setAllData] = useState([]);
    const [data, setData] = useState([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [amountInput, setAmountInput] = useState('');
    const [dateInput, setDateInput] = useState('');
    const [categoryInput, setCategoryInput] = useState('');
    const [descriptionInput, setDescriptionInput] = useState('');
    const [selectedTransactions, setSelectedTransactions] = useState([]);

    const getToday = () => {
        const today = new Date();
        return today.toISOString().split('T')[0];
    };

    let trans_url = "/djangoapp/dashboard";

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
                .filter(tx => tx.user_id === retobj.user.id);
                setAllData(transactions);
                setData(transactions);
                setUser(retobj.user);
            } else {
                setAllData([]);
                setData([]);
                setUser(null);
            }
        } catch (error) {
            console.error("Error fetching transactions:", error);
        }
        
    }

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: { display: true },
            title: { display: true, text: 'Transaction Overview' }
        },
        scales: {
            x: { title: {display: true, text: 'Date'} },
            y: { title: { display: true, text: 'Amount'} }
        }
    };

    const getChartData = () => {
        if (!Array.isArray(data) || data.length === 0) return null;

        const dateMap = {};
        data.forEach(tx => {
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

    const handleAddTransaction = async() => {
        const amount = document.querySelector('input[type="number"]').value;
        const date = document.querySelector('input[type="date"]').value || getToday();
        const description = document.querySelector('input[type="text"]').value;
        const category = document.querySelector('input[type="text"]').value || "General";

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
        setData(filtered);
    }
    
    const handleLostFocus = () => {
        if (!searchQuery) {
            setData(allData);
        }
    }
    
    useEffect(() => {
        get_transactions();
    }, []);

    useEffect(() => {
        if (data.length > 0) {
            console.log("Sample transaction:", data[0]);
        }
    }, [data]);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/');
        }
    }, [user]);

    const chartData = getChartData();
    console.log(chartData);

    return (
        <div style={{ display: 'flex', width: '100vw', minHeight: '100vh' }}>
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
        <div 
            className="dashboard-container"
            style={{
                transition: "margin-left 0.2s"
            }}
            >
            <div className="dashboard-header">
                <h1 style={{ color: '#fff' }}>Transaction Dashboard</h1>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-start', flexDirection: 'row'}}>
            <div style={{ flex: 2 }}>
                <div className="input-header">
                        <div>
                        <input 
                            type="number" 
                            placeholder="Amount" 
                            style={{ marginTop: '10px', marginLeft: '10px' }}
                            onChange={e => setAmountInput(e.target.value)}
                        />
                        <input 
                            type="text" 
                            placeholder="Description" 
                            style={{ marginTop: '10px', marginLeft: '10px' }} 
                            onChange={e => setDescriptionInput(e.target.value)}
                        />
                        <input 
                            type="text"
                            placeholder="Category"
                            style={{ marginTop: '10px', marginLeft: '10px' }}
                            onChange={e => setCategoryInput(e.target.value)}
                        />
                        <input 
                            type="date" 
                            placeholder="Date" 
                            style={{ marginTop: '10px', marginLeft: '10px' }} 
                            onChange={e => setDateInput(e.target.value)}
                        />
                        <button 
                            className="button-add" 
                            onClick={handleAddTransaction} 
                            style={{ marginTop: '10px', marginLeft: '10px' }}
                        >
                            Add
                        </button>
                        <button 
                            className="button-delete" 
                            onClick={handleDeleteTransaction} 
                            style={{ marginTop: '10px', marginLeft: '10px' }}
                        >
                            Delete
                        </button>
                    </div>
                    <div className="active-user">
                        <p style={{ marginTop: '10px' }}>{user ? user.username : "Not Logged In"}</p>
                    </div>
                </div>

            {Array.isArray(data) && data.length > 0 ? (
                <table className='data-table'>
                    <thead>
                        <tr>
                            <th></th>
                            <th>Description</th>
                            <th>Amount</th>
                            <th>Category</th>
                            <th>Date</th>
                    <th style={{ width: '150px' }}>
                        <input
                            type="text"
                            placeholder="Search transactions..."
                            onChange={handleInputChange}
                            onBlur={handleLostFocus}
                            value={searchQuery}
                        />
                    </th>
                    </tr>
                    </thead>
                    <tbody>
                        {data.map((transaction) => (
                            <tr key={transaction.id}>
                                <td>
                                    <input 
                                        type="checkbox"
                                        checked={selectedTransactions.includes(transaction.id)}
                                        onChange={() => handleCheckboxChange(transaction.id)}
                                    /></td>
                                <td>{transaction.description}</td>
                                <td>${transaction.amount}</td>
                                <td>{String(transaction.category)}</td>
                                <td>{transaction.date}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                ) : (
                    <div>
                        <p style={{ marginTop: '20px', textAlign: 'center' }}>Loading...</p>
                    </div>
            )}
            </div>
                <div style={{ flex: 1, marginLeft: '24px', minWidth: '200px' }}>
                    <h3 style={{ textAlign: 'center' }}>Transaction Overview</h3>
                    {chartData && chartData.labels && chartData.labels.length > 0 ? (
                        <Line data={chartData}  options={chartOptions}  />
                    ) : (
                        <p style={{ textAlign: 'center' }}>No data available</p>
                    )}
                </div> 
        </div>
    </div>
    </div>
    )
}
export default Dashboard;