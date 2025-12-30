import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import './Budgets.css';
import '../Dashboard/Dashboard.css';

const AddBudget = () => {
    const [ category, setCategory ] = useState("");
    const [ amount, setAmount ] = useState("");
    const [ period, setPeriod ] = useState("");
    const [ reset_day, setResetDay ] = useState(1);
    const [ expires_at, setExpiresAt ] = useState("");
    const [ user, setUser ] = useState(null);

    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        const addBudgetUrl = window.location.origin + "/djangoapp/add-budget";

        if (amount <= 0) {
            alert("Amount must be a positive number.");
            return;
        } else {
            const response = await fetch(addBudgetUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    category,
                    amount,
                    period,
                    reset_day,
                    expires_at
                }),
            });
    
            if (response.ok) {
                alert("Budget added successfully!");
                window.location.href = "/budgets"; // Redirect to budgets page
            } else {
                alert("Failed to add budget. Please try again.");
            }
        }
    };

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/');
        }
    }, [user]);

    return (
        <div className="add-budget-container">
            <div className="budget-header">
                <h2>Add New Budget</h2>
                <div className="active-user">
                        <p style={{ marginTop: '10px' }}>{user ? user.username : "Not Logged In"}</p>
                </div>
            </div>
                <form className="add-budget-form" onSubmit={handleSubmit}>
                <div>
                    <label htmlFor="budget-name">Budget Category:</label>
                    <input
                        type="text"
                        id="budget-category"
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="budget-amount">Amount:</label>
                    <input
                        type="number"
                        id="budget-amount"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="budget-period">Period:</label>
                    <select
                        id="budget-period"
                        value={period}
                        onChange={(e) => setPeriod(e.target.value)}
                        required
                    >
                        <option value="">Select a period</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                        <option value="yearly">Yearly</option>
                    </select>
                </div>
                <div>
                    <input
                        type="date"
                        value={expires_at}
                        onChange={(e) => setExpiresAt(e.target.value)}
                    />
                </div>
                {period === "monthly" ? (
                    <div>
                    <label htmlFor="budget-reset">Reset Day</label>
                    <select
                        id="reset_day"
                        value={reset_day}
                        onChange={(e) => setResetDay(Number(e.target.value))}
                    >
                        {Array.from({ length: 31 }, (_, i) => i + 1).map((reset_day) => (
                            <option key={reset_day} value={reset_day}>
                                {reset_day}
                            </option>
                        ))}
                    </select>
                </div>
                ) : (
                    <></>
                )}
                
                <button type="submit">Save Budget</button>
                </form>
            </div>
    );
};

export default AddBudget;
