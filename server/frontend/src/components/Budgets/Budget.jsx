import React, { useState, useEffect } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart, ArcElement, Tooltip, Legend, Title } from 'chart.js';
import './Budgets.css';

Chart.register(ArcElement, Tooltip, Legend, Title);

const Budget = ({ budget, transactions }) => {
    // const [collapsed, setCollapsed] = useState(true);
    // const [budget, setBudget] = useState(null);
    // const [transactions, setTransactions] = useState([]);


    // const get_transactions = async (category) => {
    //     const transactions_url = `/djangoapp/transactions?category=${category}`;
    //     try {
    //         const response = await fetch(transactions_url, {
    //             method: 'GET',
    //             credentials: 'include'
    //         });
    //         const data = await response.json();
    //         setTransactions(data.transactions || []);
    //     } catch (error) {
    //         alert('Error fetching transactions');
    //         setTransactions([]);
    //         console.error(error);
    //     }
    // }

    // const get_budget = async (budgetId) => {
    //     const budget_url = `/djangoapp/budget/${budgetId}`;
    //     try {
    //         const response = await fetch(budget_url, {
    //             method: 'GET',
    //             credentials: 'include'
    //         });
    //         if (!response.ok) {
    //             throw new Error('Budget not found');
    //         }
    //         const data = await response.json();
    //         setBudget(data.budget);
    //     } catch (error) {
    //         alert('Error fetching budget ' + budgetId);
    //         setBudget({ error: error.message });
    //         console.error(error);
    //     }
    // };

    // useEffect(() => {
    //     if (selectedBudget) {
    //         get_budget(selectedBudget);
    //     } else {
    //         // setBudget(null); // Clear budget if nothing selected
    //         setTransactions([]);
    //     }
    // }, [selectedBudgetId]);

    // useEffect(() => {
    //     if (budget && budget.name) {
    //         get_transactions(budget.name);
    //     } else {
    //         setTransactions([]);  
    //     }
    // }, [budget]);

    return (
        <div className="budget-details">
            <h3>{budget.name}</h3>
            <p>Total Budget: ${budget.amount}</p>
            <p>Amount Spent: ${transactions.reduce((acc, item) => acc + Number(item.amount), 0)}</p>
            {budget ? (
                <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {transactions.map((tx) => (
                        <tr key={tx.id}>
                            <td>{tx.date}</td>
                            <td>{tx.description}</td>
                            <td>{tx.amount}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            ) : (
                <p>Select a budget to display its details.</p>
            )}
            
            {/* {budget === null ? (
                <p>No budget selected</p>
            ) : budget.error ? (
                <p style={{ color: 'red' }}>Error: {budget.error}</p>
            ) : (
                <table className='data-table'>
                    <thead>
                        <tr>
                            <th>Transaction</th>
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
            )} */}
        </div>
    )
};

export default Budget;
