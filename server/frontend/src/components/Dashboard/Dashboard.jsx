import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import '../assets/style.css';
import Sidebar from '../Sidebar/Sidebar';
import collapsed from '../Sidebar/Sidebar';

const Dashboard = () => {
    const [allData, setAllData] = useState([]);
    const [data, setData] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");

    let trans_url = "/djangoapp/dashboard";

    const get_transactions = async () => {
        try {
                const res = await fetch(trans_url, {
                method: 'GET'
            });

            const retobj = await res.json();
            if (retobj.status === 200) {
                let transactions = Array.from(retobj.transactions);
                setAllData(transactions);
                setData(transactions);
            } else {
                setData([]);
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

    const handleAddTransaction = () => {
        const amount = document.querySelector('input[type="number"]').value;
        const date = document.querySelector('input[type="date"]').value;
        const description = document.querySelector('input[type="text"]').value;

        // Add validation if needed

        const newTransaction = {
            amount: parseFloat(amount),
            date: date,
            description: description
        };

        // Send the new transaction to the backend
        fetch(trans_url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newTransaction)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 201) {
                // Transaction added successfully
                setData([...data, newTransaction]);
            }
        });
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
        
        <div className="dashboard-container">
            <Sidebar />
            <h1 style={{ marginLeft: collapsed ? "80px" : "200px", textAlign: 'center' }}>Transaction Dashboard</h1>
            <div className="dashboard-header" style={{ marginLeft: collapsed ? "80px" : "200px" }}>
                <input type="number" placeholder="Amount" style={{ marginTop: '10px', marginLeft: '10px' }} />
                <input type="date" placeholder="Date" style={{ marginTop: '10px', marginLeft: '10px' }} />
                <input type="text" placeholder="Description" style={{ marginTop: '10px', marginLeft: '10px' }} />
                <button className="button"onClick={handleAddTransaction} style={{ marginTop: '10px', marginLeft: '10px' }}>Add</button>
            </div>
            {data ? (
                <table className='data-table' style={{ marginLeft: collapsed ? "80px" : "250px" }}>
                    <tr>
                        <th>ID</th>
                        <th>Description</th>
                        <th>Amount</th>
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
                            <tr>
                                <td>{transaction.id}</td>
                                <td>{transaction.description}</td>
                                <td>${transaction.amount}</td>
                            </tr>
                        ))}
                    </table>
                ) : (
                    <div>
                        <p style={{ marginLeft: collapsed ? '80px' : '250px' , marginTop: '20px', textAlign: 'center' }}>Loading...</p>
                    </div>
            )}
        </div>
    )
}
export default Dashboard;