import React, { useState, useEffect } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart, ArcElement, Tooltip, Legend, Title } from 'chart.js';
import './Budgets.css';

Chart.register(ArcElement, Tooltip, Legend, Title);

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

    const getPieChartData = (budget, transactions) => {
        if (!budget || !budget.name || transactions.length === 0) return {};

        const dataByCategory = {};
        
        // budget.name

        const categoryTotals = transactions.reduce((acc, tx) => {
            acc[tx.category] = (acc[tx.category] || 0) + tx.amount;
            return acc;
        }, {});

        const totalSpent = Object.values(categoryTotals).reduce((sum, val) => sum + val, 0);
        const remaining = Math.max(budget.amount - totalSpent, 0);
        categoryTotals['Remaining'] = remaining;
        categoryTotals['Total Spent'] = totalSpent;

        const colors = [
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 206, 86, 0.6)',
        ];

        return {
            labels: Object.keys(categoryTotals),
            datasets: [
                {
                    data: Object.values(categoryTotals),
                    backgroundColor: colors.slice(0, Object.keys(categoryTotals).length),
                    borderWidth: 1,
                }
            ]
        };
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
        <div className="budget-details">
            {budget === null ? (
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
            )}
        </div>
    )
};

export default Budget;
