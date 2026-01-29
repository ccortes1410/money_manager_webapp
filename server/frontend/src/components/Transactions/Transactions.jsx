import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";
import "../assets/bootstrap.min.css";
import "../assets/style.css";
import "./Transactions.css";
import { AuthContext } from '../../AuthContext';    

const Transactions = () => {
    const [data, setData] = useState([]);
    const [allData, setAllData ] = useState([]);
    const { user } = useContext(AuthContext);
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
                .filter(tx => tx.user_id === user.id);
                setAllData(transactions);
                setData(transactions);
            } else {
                setAllData([]);
                setData([]);
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

    // useEffect(() => {
    //     if (data.length > 0) {
    //         console.log("Transactions data updated:", data);
    //     }
    // }, [data]);
    
    // useEffect(() => {
    //     if (user !== null && !user.is_authenticated) {
    //         navigate("/login");
    //     }
    // }, [user]);

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
        <div className="tx-input-header">
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
                        <input
                            id='amount-input'
                            className='tx-text-input'
                            type="number"
                            placeholder='Amount'
                            value={amountInput}
                            onChange={(e) => setAmountInput(e.target.value)}
                        />
                        <input
                            id='description-input'
                            className='tx-text-input'
                            type="text"
                            placeholder='Description'
                            value={descriptionInput}
                            onChange={(e) => setDescriptionInput(e.target.value)}
                        />
                        <input
                            id='category-input'
                            className='tx-text-input'
                            type="text"
                            placeholder='Category'
                            value={categoryInput}
                            onChange={(e) => setCategoryInput(e.target.value)}
                        />
                        <input
                            id='date-input'
                            className='tx-date-input'
                            type="date"
                            value={dateInput}
                            onChange={(e) => setDateInput(e.target.value)}
                        />
                        <button
                            className="add-btn"
                            onClick={handleAddTransaction}
                        >
                            +
                        </button>
                        <button
                            className="del-btn"
                            onClick={() => handleDeleteTransaction(selectedTransactions)}
                            style={{ marginLeft: '10px' }}
                        >
                            -
                        </button>
                    </div>
            </div>
            {/* <div> */}
                {Array.isArray(data) && data.length > 0 ? (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Description</th>
                                <th>Amount</th>
                                <th>Category</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.map((transaction) => {
                                const isSelected = selectedTransactions?.id === transaction.id;

                                return (
                                    <tr 
                                        key={transaction.id}
                                        className={
                                            setSelectedTransactions?.id === transaction.id ? "selected-row" : ""
                                        }
                                        onClick={() => setSelectedTransactions(isSelected ? null : transaction)}
                                    >      
                                    {/* <td style={{ width: '30px'}}>
                                        <input
                                            type="checkbox"
                                            checked={selectedTransactions.includes(transaction.id)}
                                            onChange={() => handleCheckboxChange(transaction.id)}
                                        /> 
                                    </td>*/}
                                    <td>{transaction.description}</td>
                                    <td>${transaction.amount}</td>
                                    <td>{String(transaction.category)}</td>
                                    <td>{transaction.date}</td>
                                </tr>
                            )}
                            )}
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