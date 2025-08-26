import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import '../assets/style.css';


const Dashboard = () => {
    const [data, setData] = useState(null);

    let trans_url = "/djangoapp/get_transactions";

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

    
    return (
        <div className="dashboard">
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
                    <p>Loading...</p>
            )}
        </div>
    )
}
export default Dashboard;