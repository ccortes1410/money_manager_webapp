import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import '../assets/style.css';
import Sidebar from '../Sidebar/Sidebar';
import collapsed from '../Sidebar/Sidebar';

const Dashboard = () => {
    const [data, setData] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");

    let trans_url = "/djangoapp/dashboard";

    const get_transactions = async () => {
        const res = await fetch(trans_url, {
            method: 'GET'
        });

        const retobj = await res.json();
        if (retobj.status === 200) {
            let transactions = Array.from(retobj.transactions);
            setData(transactions);
        }
    }
    useEffect(() => {
        get_transactions();
    }, []);

    const handleAddTransaction = () => {

    }

    const handleInputChange = (e) => {
        const query = e.target.value;
        setSearchQuery(query);
        const filtered = data.filter((transaction) =>
            transaction.description.toLowerCase().includes(query.toLowerCase())
        );
        setData(filtered);
    }
    
    const handleLostFocus = () => {
        if (!searchQuery) {
            setData(data);
        }
    }
    
    return (
        
        <div className="dashboard-container">
            <Sidebar />
            <div className="dashboard-header" style={{ marginLeft: collapsed ? "80px" : "200px" }}>
                <input type="button" value="Add Transaction" onClick={handleAddTransaction} />
            </div>
            <h1>Transaction Dashboard</h1>
            {data ? (
                <table className='table'>
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
                    <p style={{ marginLeft: '250px' , marginTop: '20px', textAlign: 'center' }}>Loading...</p>
            )}
        </div>
    )
}
export default Dashboard;