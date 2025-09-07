import React, { useState } from "react";
import Sidebar from '../Sidebar/Sidebar';
import './Budgets.css';
import '../Dashboard/Dashboard.css';

const AddBudget = () => {
    const [name, setName] = useState("");
    const [amount, setAmount] = useState("");
    const [period, setPeriod] = useState("");
    const [collapsed, setCollapsed] = useState(true); 
    const [user, setUser] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        const addBudgetUrl = window.location.origin + "/djangoapp/add-budget";
        const response = await fetch(addBudgetUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name,
                amount,
                period
            }),
        });

        if (response.ok) {
            alert("Budget added successfully!");
            window.location.href = "/budgets"; // Redirect to budgets page
        } else {
            alert("Failed to add budget. Please try again.");
        }
    };

    return (
        <div style={{ display: 'flex', width: '100vw', minHeight: '100vh', overflow: 'hidden' }}>
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
            <div className="add-budget-container">
            <div className="budget-header">
                <h2>Add New Budget</h2>
                <div className="active-user">
                        <p style={{ marginTop: '10px' }}>{user ? user.username : "Not Logged In"}</p>
                </div>
            </div>
                <form className="add-budget-form" onSubmit={handleSubmit}>
                <div>
                    <label>Budget Name:</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label>Amount:</label>
                    <input
                        type="number"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label>Period:</label>
                    <select
                        value={period}
                        onChange={(e) => setPeriod(e.target.value)}
                        required
                    >
                        <option value="">Select a period</option>
                        <option value="monthly">Monthly</option>
                        <option value="yearly">Yearly</option>
                    </select>
                </div>
                <button type="submit">Add Budget</button>
                </form>
            </div>
        </div>
    );
};

export default AddBudget;
