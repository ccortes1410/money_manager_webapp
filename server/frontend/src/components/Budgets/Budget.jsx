import React, { useState, useEffect } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart, ArcElement, Tooltip, Legend, Title } from 'chart.js';
import './Budgets.css';

Chart.register(ArcElement, Tooltip, Legend, Title);

const Budget = ({ budget }) => {

    if (!budget) {
        return (
            <div className="budget-details empty">
                <p>Select a budget to display its details.</p>
            </div>
        )
    }

    if (!Array.isArray(budget.transactions)) {
        return <p>No transactions for this budget</p>
    }
    
    // const get_budget = async (budget) => {
    //     const budget_url = `/djangoapp/budgets/${budget.id}`;
    //     try {
    //         const response = await fetch(budget_url, {
    //             method: 'GET',
    //             credentials:'include',
    //             headers: {
    //                 'Content-Type': 'application/json'
    //             }
    //         });
            
    //         const data = await response.json()

    //         if (!response.ok) {
    //             throw new Error("Error fetching budget")
    //         }

    //         if (data.budget && data.isArray(data.budget)) {
    //             setBudgetDetail(data.budget)
    //         }

    //     } catch (error) {
    //         console.log("Couldn't fetch budget:", error)
    //         setBudgetDetail([])
    //     }
    // }

    console.log("Budget spent: ", budget.spent)
    console.log("Remaining budget:", budget.remaining)

    return (
        <div className="budget-details">
            <h3>{budget.category}</h3>
            <p>Total Budget: ${budget.amount}</p>
            <p>Amount Spent: ${budget.spent}</p>
                <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {budget.transactions.map((tx) => (
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
