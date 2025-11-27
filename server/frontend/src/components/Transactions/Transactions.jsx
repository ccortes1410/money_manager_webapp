import React, { useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";
import "../assets/bootstrap.min.css";
import "../assets/style.css";
import "./Transactions.css";
import Sidebar from '../Sidebar/Sidebar';

const Transactions = () => {
    const [collapsed, setCollapsed] = useState(true);
    const [data, setData] = useState([]);
    const [allData, setAllData ] = useState([]);
    const [user, setUser] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [amountInput, setAmountInput] = useState("");
    const [dateInput, setDateInput] = useState("");
    const [categoryInput, setCategoryInput] = useState("");
    const [descriptionInput, setDescriptionInput] = useState("");
    const [selectedTransactions, setSelectedTransactions] = useState([]);

    const getToday = () => {
        const today = new Date();
        return today.toISOString().split('T')[0];
    }

    let transaction_url = "/djangoapp/transactions";

    const navigate = useNavigate();

    const get_transactions = async () => {
        try {
            const res = await fetch(transaction_url, {
                method: 'GET',
                credentials: 'include'
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

    const handleAddTransaction = async () => {
        const amount = amountInput;
        const date = dateInput || getToday();
        const category = categoryInput;
        const description = descriptionInput || "General";

        const newTransaction = {
            amount: parseFloat(amount),
            date: date,
            category: category,
            description: description
        };

        try {
            const res = await fetch(transaction_url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newTransaction),
                credentials: 'include'
            });
            const result = await res.json();

            if (res.ok || result.ok) {
                get_transactions();
                setAmountInput("");
                setDateInput("");
                setCategoryInput("");
                setDescriptionInput("");
            } else {
                console.error("Failed to add transaction");
            }
        } catch (error) {
            console.error("Error adding transaction:", error);
        }
    };

    const handleCheckboxChange = (id) => {
        setSelectedTransactions(prevSelected => 
            prevSelected.includes(id) ?
            prevSelected.filter(txId => txId !== id) :
            [...prevSelected, id]
        );
    };

    const handleDeleteTransaction = async () => {
        if (selectedTransactions.length === 0) return;
        try {
            const res = await fetch(transaction_url, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ ids: selectedTransactions })
            });
            if (res.ok) {
                get_transactions();
                setSelectedTransactions([]);
            } else {
                alert("Failed to delete transactions");
            }
        } catch (error) {
            console.error("Error deleting transactions:", error);
        }
    }

    const handleInputChange = (e) => {
        const query = e.target.value;
        setSearchQuery(query);

        const filtered = allData.filter((tx) =>
            tx.description.toLowerCase().includes(query.toLowerCase())
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
    }, []);

    useEffect(() => {
        if (data.length > 0) {
            console.log("Transactions data updated:", data);
        }
    }, [data]);
    
    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate("/login");
        }
    }, [user]);

    return (
        // <div style={{ display: 'flex', width: '100vw', minHeight: '100vh', overflow: 'hidden' }} >
        //     <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
        <div
            className="transactions-container"
        >
            <div className="transactions-header">
                <h1 style={{ color: '#fff' }}>Transactions</h1>
                <div className="active-user">
                    <p style={{ marginTop: '10px' }}>{user ? user.username : "Not Logged In"}</p>
                </div>
        </div>
        <div className="input-header">
            <div>
                <input
                    type="number"
                    placeholder="Amount"
                    style={{ marginTop: '10px' , marginLeft: '10px' }}
                    value={amountInput}
                    onChange={(e) => setAmountInput(e.target.value)}
                />
                <input 
                    type="text"
                    placeholder="Description"
                    style={{ marginTop: '10px' , marginLeft: '10px' }}
                    value={descriptionInput}
                    onChange={(e) => setDescriptionInput(e.target.value)}
                />
                <input
                    type="text"
                    placeholder="Category"
                    style={{ marginTop: '10px' , marginLeft: '10px' }}
                    value={categoryInput}
                    onChange={(e) => setCategoryInput(e.target.value)}
                />
                <input
                    type="date"
                    style={{ marginTop: '10px' , marginLeft: '10px' }}
                    value={dateInput}
                    onChange={(e) => setDateInput(e.target.value)}
                />
                <button
                    className="button-add"
                    onClick={handleAddTransaction}
                    style={{ marginTop: '10px' , marginLeft: '10px' }}
                >
                    +
                </button>
                <button
                    className="button-delete"
                    onClick={handleDeleteTransaction}
                    style={{ marginTop: '10px' , marginLeft: '10px' }}
                >
                    -
                </button>
                <input
                    type="text"
                    placeholder="Search"
                    onChange={handleInputChange}
                    onBlur={handleLostFocus}
                    value={searchQuery}
                    />
            </div>
            </div>
            {/* <div> */}
                {Array.isArray(data) && data.length > 0 ? (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Select</th>
                                <th>Description</th>
                                <th>Amount</th>
                                <th>Category</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.map((transaction) => (
                                <tr key={transaction.id}>
                                    <td style={{ width: '30px'}}>
                                        <input
                                            type="checkbox"
                                            checked={selectedTransactions.includes(transaction.id)}
                                            onChange={() => handleCheckboxChange(transaction.id)}
                                        />
                                    </td>
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
        // </div>
        // </div>
    )
}

export default Transactions;