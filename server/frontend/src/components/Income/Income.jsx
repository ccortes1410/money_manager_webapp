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

        const allYears = income.flatMap(item => {
            const start = parseYearMonth(item.period_start);
            const end = parseYearMonth(item.period_end);
            if (!start || !end) return [];
            return [start, end];
        });

        if (!allYears.length) return [];

        const minYear = Math.min(...allYears);
        const maxYear = Math.max(...allYears);

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
        if (!dateStr || typeof dateStr !== "string") {
            return null;
        }

        const parts = dateStr.split("-");
        if (parts.length < 2) {
            return null;
        }

        const year = Number(parts[0]);
        const monthIndex = Number(parts[1]) - 1;

        if (Number.isNaN(year) || Number.isNaN(monthIndex)) {
            return null;
        }

        return { year, monthIndex };
    };


    const selectedPeriod = selectedIncome
        ? (() => {
            const start = parseYearMonth(selectedIncome.period_start);
            const end = parseYearMonth(selectedIncome.period_end);

            if (!start || !end) return null;
            return { start, end };
        })()
        : null;
    
    const monthsRefs = useRef({});

    function isMonthInPeriod(year, monthIndex, start, end) {
        const value = year * 12 + monthIndex;
        const startValue = start.year * 12 + start.monthIndex;
        const endValue = end.year * 12 + end.monthIndex;

        return value >= startValue && value <= endValue;
    }
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

    useEffect(() => {
        if (!selectedPeriod) return;

        const { start } = selectedPeriod;
        const key = `${start.year}-${start.monthIndex}`;
        const el = monthsRefs.current[key]
        console.log("Ref exists:", monthsRefs.current[key]);
        console.log("Scroll key:", `${selectedPeriod.start.year}-${selectedPeriod.start.monthIndex}`);
        if (el) {
            el.scrollIntoView({
                behavior: "smooth",
                block: "center",
            });
        }
    },[selectedPeriod]);

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

    console.log("Parsed date:", selectedPeriod);

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
                                        {MONTHS.map((_, index) => {
                                            const isHighlighted =
                                                selectedPeriod &&
                                                isMonthInPeriod(
                                                    year,
                                                    index,
                                                    selectedPeriod.start,
                                                    selectedPeriod.end
                                                );
                                            return (
                                                <li 
                                                key={`${year}-${index}`} 
                                                ref={(el) => {
                                                    if (el) monthsRefs.current[`${year}-${index}`] = el;
                                                }}
                                                className={`month-item ${
                                                    isHighlighted ? "highlighted-month" : ""
                                                }`}
                                            >
                                                {MONTHS[index]}
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
                    <div 
                        className="income-table-inputs"
                        >
                        <input
                            id='amount-input'
                            className='inc-text-input'
                            type="number"
                            placeholder='Amount'
                            value={amountInput}
                            onChange={(e) => setAmountInput(e.target.value)}
                        />
                        <input
                            id='source-input'
                            className='inc-text-input'
                            type="text"
                            placeholder='Source'
                            value={sourceInput}
                            onChange={(e) => setSourceInput(e.target.value)}
                        />
                        <label
                            className="date-label"
                            >
                            Date Received
                            <input
                                id="date-recevied-input"
                                className="inc-text-input"
                                type="date"
                                value={dateReceivedInput}
                                onChange={(e) => setDateReceivedInput(e.target.value)}
                            />
                        </label>
                        <label
                            className="date-label"
                            >
                            Period Start
                            <input
                                id="start-date-input"
                                className="inc-text-input"
                                type="date"
                                value={periodStart}
                                onChange={(e) => setPeriodStart(e.target.value)}
                            />
                        </label>
                        <label 
                            className="date-label"
                            >
                            Period End
                            <input
                                id="end-date-input"
                                className="inc-text-input"
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

