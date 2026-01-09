import React, { useState, useEffect, useContext } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../../AuthContext";
import "./Income.css";

const Income = () => {
    const [amountInput, setAmountInput] = useState("");
    const [dateReceivedInput, setDateReceivedInput] = useState("");
    const [dateIntendedInput, setDateIntendedInput] = useState("");
    const [sourceInput, setSourceInput] = useState("");
    const [data, setData] = useState([]);
    const { user } = useContext(AuthContext);
    const [selectedIncome, setSelectedIncome] = useState([]);

    const navigate = useNavigate();

    const income_url = "/djangoapp/income";

    const getToday = () => {
        const today = new Date();
        return today.toISOString().split('T')[0];
    }

    const get_income = async () => {
        try {
            const res = await fetch(income_url, {
                method: "GET",
                credentials: "include",
            });

            const retobj = await res.json();
            if (retobj.incomes && Array.isArray(retobj.incomes)) {
                let income_list = Array.from(retobj.incomes)
                .filter(inc => inc.user_id === retobj.user.id);
                setData(income_list);
                console.log("Fetched income data:", JSON.stringify(income_list, null, 4));
            } else {
                setData([]);
                console.log("No income data found for user ", user);
            }
        } catch (error) {
            console.error("Error fetching income data:", error);
    }
    }

    const handleAddIncomeSource = async () => {
        const amount = amountInput;
        const date_received = dateReceivedInput || getToday();
        const date_intended = dateIntendedInput;
        const source = sourceInput;

        const newIncome = {
            amount: parseFloat(amount),
            date_received: date_received,
            date_intended: date_intended,
            source: source,
        };

        try {
            const res = await fetch(income_url, {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(newIncome),
            });

            if (res.ok) {
                get_income();
                setAmountInput("");
                setDateReceivedInput("");
                setDateIntendedInput("");
                setSourceInput("");
            } else {
                console.error("Error adding income source:", res.statusText);
            }
        } catch (error) {
            console.error("Error adding income source:", error);
        }
    }

    const handleDeleteIncome = async (incomeId) => {
        if (selectedIncome.length === 0) return;
        try {
            const res = await fetch(income_url, {
                method: "DELETE",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ income_ids: selectedIncome }),
            });

            if (res.ok) {
                get_income();
                setSelectedIncome([]);
            }
        } catch (error) {
            console.error("Error deleting income source:", error);
        }
    }

    const handleCheckboxChange = (id) => {
        setSelectedIncome((prevSelected) =>
            prevSelected.includes(id) ?
            prevSelected.filter(incId => incId !== id) :
            [...prevSelected, id]
        );
    };

    useEffect(() => {
        get_income();
    }, []);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate("/");
        }
    }, [user]);

    return (
        <div className="income-container">
            <div className="income-header">
                <h1>Income</h1>
                <div className="active-user">
                    <p style={{ marginTop: '10px' }}>{user ? user.username : "Not Logged In"}</p>
                </div>
            </div>

            <div className='income-table-container'>
                <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
                    <input
                        id='amount-input'
                        className='subs-text-input'
                        type="number"
                        placeholder='Amount'
                        value={amountInput}
                        onChange={(e) => setAmountInput(e.target.value)}
                    />
                    <input
                        id='source-input'
                        className='subs-text-input'
                        type="text"
                        placeholder='Source'
                        value={sourceInput}
                        onChange={(e) => setSourceInput(e.target.value)}
                    />
                    <input
                        id='category-input'
                        className='subs-text-input'
                        type="date"
                        value={dateReceivedInput}
                        onChange={(e) => setDateReceivedInput(e.target.value)}
                    />
                    <input
                        id='date-input'
                        className='date-input'
                        type="date"
                        value={dateIntendedInput}
                        onChange={(e) => setDateIntendedInput(e.target.value)}
                    />
                    <button
                        className="add-btn"
                        onClick={handleAddIncomeSource}
                    >
                        +
                    </button>
                    <button
                        className="del-btn"
                        onClick={() => handleDeleteIncome(selectedIncome)}
                        style={{ marginLeft: '10px' }}
                    >
                        -
                    </button>
                </div>
                {Array.isArray(data) && data.length > 0 ? (
                    <table className="income-table">
                    <thead>
                        <tr>
                            <th></th>
                            <th>Amount</th>
                            <th>Source</th>
                            <th>Date Received</th>
                            <th>Date Intended</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((income) => (
                            <tr key={income.id}>
                                <td>
                                    <input
                                        type="checkbox"
                                        checked={selectedIncome.includes(income.id)}
                                        onChange={() => handleCheckboxChange(income.id)}
                                    />
                                </td>
                                <td>${Number(income.amount)}</td>
                                <td>{income.source}</td>
                                <td>{income.date_received}</td>
                                <td>{income.date_intended}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                ) : (
                <p className="no-income-message">No income sources found. Please add an income source.</p>
                )}
                
            </div>
        </div>
    )
}

export default Income;

