import React, { useState, useEffect } from 'react';
import Sidebar from '../Sidebar/Sidebar';
import '../Dashboard/Dashboard.css';

const Budget = ({ selectedBudgetId }) => {
    // const [collapsed, setCollapsed] = useState(true);
    const [budget, setBudget] = useState(null);
    const [transactions, setTransactions] = useState([]);


    const get_transactions = async (category) => {
        const transactions_url = `/djangoapp/dashboard?category=${category}`;
        try {
            const response = await fetch(transactions_url, {
                method: 'GET',
                credentials: 'include'
            });
            const data = await response.json();
            setTransactions(data.transactions || []);
        } catch (error) {
            alert('Error fetching transactions');
            setTransactions([]);
            console.error(error);
        }
    }

    const get_budget = async (budgetId) => {
        const budget_url = `/djangoapp/budget/${budgetId}`;
        try {
            const response = await fetch(budget_url, {
                method: 'GET',
                credentials: 'include'
            });
            if (!response.ok) {
                throw new Error('Budget not found');
            }
            const data = await response.json();
            setBudget(data.budget);
        } catch (error) {
            alert('Error fetching budget ' + budgetId);
            setBudget({ error: error.message });
            console.error(error);
        }
    };
    useEffect(() => {
        if (selectedBudgetId) {
            get_budget(selectedBudgetId);
        } else {
            setBudget(null); // Clear budget if nothing selected
            setTransactions([]);
        }
    }, [selectedBudgetId]);

    useEffect(() => {
        if (budget && budget.name) {
            get_transactions(budget.name);
        } else {
            setTransactions([]);  
        }
    }, [budget]);

    return (
            <div className="budget-container">
                <h2>Budget Details</h2>
                {budget === null ? (
                    <p>No budget selected</p>
                ) : budget.error ? (
                    <p style={{ color: 'red' }}>Error: {budget.error}</p>
                ) : (
                    <div>
                        <h3>{budget.name}</h3>
                            <p>Amount: ${budget.amount}</p>
                            <p>Period: {budget.period}</p>
                            <h4>Transactions</h4>
                                {transactions.length === 0 ? (
                                    <p>No transactions found</p>
                                ) : (
                                    <table className='data-table'>
                                        <thead>
                                            <tr>
                                                <th>Description</th>
                                                <th>Amount</th>
                                                <th>Date</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {transactions.map((tx) => (
                                                <tr key={tx.id}>
                                                    <td>{tx.description}</td>
                                                    <td>${tx.amount}</td>
                                                    <td>{tx.date}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                        </div>
                    )
                }
            </div>
    );
}

export default Budget;
