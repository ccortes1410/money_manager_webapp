import React, { useRef, useState, useEffect, useContext, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../../AuthContext";
import "./Income.css";

const Income = () => {
    const [ amountInput, setAmountInput ] = useState("");
    const [ dateReceivedInput, setDateReceivedInput ] = useState("");
    const [ periodStart, setPeriodStart ] = useState("");
    const [ periodEnd, setPeriodEnd ] = useState("");
    const [ sourceInput, setSourceInput ] = useState("");
    const [ income, setIncome ] = useState([]);
    const [ transactions, setTransactions ] = useState([]);
    const { user } = useContext(AuthContext);
    const [ selectedIncome, setSelectedIncome ] = useState([]);

    const navigate = useNavigate();

    const income_url = "/djangoapp/income";

    const getToday = () => {
        const today = new Date();
        return today.toISOString().split('T')[0];
    }

    // Fetch income data for the logged-in user
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
                setIncome(income_list);
                // console.log("Fetched income data:", JSON.stringify(income_list, null, 4));
            } else {
                setIncome([]);
                console.log("No income data found for user ", user);
            }
        } catch (error) {
            console.error("Error fetching income data:", error);
        }
    }
    // Fetch transaction data for the logged-in user
    const get_transactions = async () => {
        try {
            const res = await fetch("/djangoapp/transactions", {
                method: "GET",
                credentials: "include",
            });
            const retobj = await res.json();
            if (retobj.transactions && Array.isArray(retobj.transactions)) {
                let transaction_list = Array.from(retobj.transactions)
                .filter(txn => txn.user_id === retobj.user.id);
                setTransactions(transaction_list);
                // Process transactions as needed
            } else {
                console.log("No transaction data found for user ", user);
            }
        } catch (error) {
            console.error("Error fetching transaction data:", error);
        }
    }
    // Calculate total income and remaining funds
    const totalIncome = useMemo(() => {
        return income.reduce(
            (total, inc) => total + parseFloat(inc.amount), 0);
    }, [income]);

    const totalSpent = useMemo(() => {
        return transactions.reduce(
            (sum, tx) => sum + Number(tx.amount),
            0
        );
    }, [transactions]);

    const remainingFunds = totalIncome - totalSpent;

    const percentageRemaining = totalIncome > 0
        ? Math.max(0, (remainingFunds / totalIncome) * 100)
        : 0;

    const YEARS = Array.from({ length: 10 }, (_, i) => 2024 + i);

    const years = useMemo(() => {
        if (!income.length) return [];

        const yearsFromData = income.flatMap(item => {
            const start = new Date(item.period_start + "T00:00:00Z").getUTCFullYear();
            const end = new Date(item.period_end + "T00:00:00Z").getUTCFullYear();
            return [start, end];
        });

        const minYear = Math.min(...yearsFromData);
        const maxYear = Math.max(...yearsFromData);

        return Array.from(
            { length: maxYear - minYear +1 },
            (_, i) => minYear + i
        );
    }, [income]);


    const MONTHS = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    function parseYearMonth(dateStr) {
        const date = new Date(dateStr + "T00:00:00Z");
        return {
            year: date.getUTCFullYear(),
            month: date.getUTCMonth(), // 0–11
        };
    }

    const selectedDate = selectedIncome
        ? parseYearMonth(selectedIncome.date_intended)
        : null;
    
    const monthsRefs = useRef({});

    // Add a new income source
    const handleAddIncomeSource = async () => {
        const amount = amountInput;
        const date_received = dateReceivedInput || getToday();
        const period_start = periodStart;
        const period_end = periodEnd;
        const source = sourceInput;

        const newIncome = {
            amount: parseFloat(amount),
            date_received: date_received,
            period_start: period_start,
            period_end: period_end,
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
                setPeriodStart("");
                setPeriodEnd("");
                setSourceInput("");
            } else {
                console.error("Error adding income source:", res.statusText);
            }
        } catch (error) {
            console.error("Error adding income source:", error);
        }
    }
    // Delete selected income sources
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
    // Handle checkbox selection for income sources
    // const handleCheckboxChange = (id) => {
    //     setSelectedIncome((prevSelected) =>
    //         prevSelected.includes(id) ?
    //         prevSelected.filter(incId => incId !== id) :
    //         [...prevSelected, id]
    //     );
    // };

    useEffect(() => {
        if (!selectedDate) return;

        const key = `${selectedDate.year}-${selectedDate.month}`;
        const el = monthsRefs.current[key]
        console.log("Ref exists:", monthsRefs.current[key]);

        if (el) {
            el.scrollIntoView({
            behavior: "smooth",
            block: "center",
        });
    }
    },[selectedDate]);

    // Initial data fetch and authentication check
    useEffect(() => {
        get_income();
        get_transactions();
    }, []);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate("/");
        }
    }, [user]);

    if (new Date(periodEnd) < new Date(periodStart)) {
        alert ("End date cannot be before start date");
        return;
    }

    function isMonthInRange(year, month, start, end) {
        const date = new Date(year,month,1);
        return date >= start && date <= end;
    }

    console.log("Parsed date:", selectedDate);
    console.log("Scroll key:", `${selectedDate.year}-${selectedDate.month}`);

    return (
        <div className="income-container">
            <div className="income-header">
                <h1>Income</h1>
                <div className="active-user">
                    <p style={{ marginTop: '10px' }}>{user ? user.username : "Not Logged In"}</p>
                </div>
            </div>
            <div className="income-layout">
                <div className="income-calendar-col">
                    <div className="income-calendar-container">
                        {YEARS.map((year) => (
                            <div key={year} className="calendar-year">
                                <div className="year-header">{year}</div>
                                    <ul className="months-list">
                                        {MONTHS.map((month, index) => {
                                            const isHighlighted =
                                                selectedIncome &&
                                                isMonthInRange(
                                                    year,
                                                    index,
                                                    new Date(selectedIncome.period_start),
                                                    new Date(selectedIncome.period_end)
                                                );
                                            return (
                                                <li 
                                                key={`${year}-${index}`} 
                                                className={`month-item ${
                                                    isHighlighted ? "highlighted-month" : ""
                                                }`}
                                            >
                                                {month}
                                            </li>
                                            );
                                        })}  
                                    </ul>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="income-bar-col">
                    <div className="income-bar-wrapper">
                        <div className="income-progress-bar">
                            <div 
                                className="income-progress-fill"
                                style={{ height: `${percentageRemaining}%` }}>
                                {/* Future feature: Dynamic fill based on income goals */}
                            </div>
                        </div>
                        <h2>Funds</h2>
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
                        <label>
                            Date Received
                            <input
                                id="date-recevied-input"
                                className="subs-text-input"
                                type="date"
                                value={dateReceivedInput}
                                onChange={(e) => setDateReceivedInput(e.target.value)}
                            />
                        </label>
                        <label>
                            Period Start
                            <input
                                id="start-date-input"
                                className="subs-text-input"
                                type="date"
                                value={periodStart}
                                onChange={(e) => setPeriodStart(e.target.value)}
                            />
                        </label>
                        <label>
                            Period End
                            <input
                                id="end-date-input"
                                className="subs-text-input"
                                type="date"
                                value={periodEnd}
                                onChange={(e) => setPeriodEnd(e.target.value)}
                            />
                        </label>
                        
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
                    {Array.isArray(income) && income.length > 0 ? (
                        <table className="income-table">
                        <thead>
                            <tr>
                                <th>Amount</th>
                                <th>Source</th>
                                <th>Date Received</th>
                                <th>Applies to</th>
                            </tr>
                        </thead>
                        <tbody>
                            {income.map((inc) => {
                                const isSelected = selectedIncome?.id === inc.id;

                                return (
                                    <tr 
                                    key={inc.id}
                                    className={
                                        selectedIncome?.id === inc.id ? "selected-row" : ""
                                    }
                                    onClick={() => setSelectedIncome(isSelected ? null : inc)}
                                >
                                    <td>${Number(inc.amount)}</td>
                                    <td>{inc.source}</td>
                                    <td>{inc.date_received}</td>
                                    <td>{inc.period_start}:{inc.period_end} </td>
                                </tr>
                                )                                
                            })}
                        </tbody>
                    </table>
                    ) : (
                    <p className="no-income-message">No income sources found. Please add an income source.</p>
                    )}
                    
                </div>
            </div>
        </div>
    )
}

export default Income;

