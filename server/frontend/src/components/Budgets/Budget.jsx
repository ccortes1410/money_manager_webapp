import React, { useState, useEffect } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart, ArcElement, Tooltip, Legend, Title } from 'chart.js';
import './Budgets.css';

Chart.register(ArcElement, Tooltip, Legend, Title);

const Budget = ({ budget, transactions }) => {

    if (!budget) {
        return (
            <div className="budget-details empty">
                <p>Select a budget to display its details.</p>
            </div>
        )
    }

    return (
        <div className="budget-details">
            <h3>{budget.category}</h3>
            <p>Total Budget: ${budget.amount}</p>
            <p>Amount Spent: ${transactions.reduce((acc, item) => acc + Number(item.amount), 0)}</p>
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
