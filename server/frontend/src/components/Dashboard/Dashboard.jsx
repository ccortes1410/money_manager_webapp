import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';
import '../assets/style.css';
import Sidebar from '../Sidebar/Sidebar';

const Dashboard = () => {
    const [collapsed, setCollapsed] = useState(true);
    const [user, setUser] = useState(null);
    const [allData, setAllData] = useState([]);
    const [data, setData] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [amountInput, setAmountInput] = useState('');
    const [dateInput, setDateInput] = useState('');
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
                let transactions = Array.from(retobj.transactions);
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

    useEffect(() => {
        get_transactions();
    }, []);

    useEffect(() => {
        console.log("data:", data);
    }, [data]);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/');
        }
    }, [user]);

    const handleAddTransaction = async() => {
        const amount = document.querySelector('input[type="number"]').value;
        const date = document.querySelector('input[type="date"]').value || getToday();
        const description = document.querySelector('input[type="text"]').value;

        // Add validation if needed

        const newTransaction = {
            amount: parseFloat(amount),
            date: date,
            description: description
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
    
    return (
        <div style={{ display: 'flex', width: '100vw', minHeight: '100vh' }}>
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
        <div 
            className="dashboard-container"
            style={{
                transition: "margin-left 0.2s"
            }}
            >
            <h1 style={{textAlign: 'center' }}>Transaction Dashboard</h1>
            <div className="dashboard-header">
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
            
            {data ? (
                <table className='data-table'>
                    <tr>
                        <th></th>
                        <th>Description</th>
                        <th>Amount</th>
                        <th>Date</th>
                    <th>
                        <input
                            type="text"
                            placeholder="Search transactions..."
                            onChange={handleInputChange}
                            onBlur={handleLostFocus}
                            value={searchQuery}
                        />
                    </th>
                    </tr>
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
                                <td>{transaction.date}</td>
                            </tr>
                        ))}
                    </table>
                ) : (
                    <div>
                        <p style={{ marginTop: '20px', textAlign: 'center' }}>Loading...</p>
                    </div>
            )}
        </div>
        </div>
    )
}
export default Dashboard;