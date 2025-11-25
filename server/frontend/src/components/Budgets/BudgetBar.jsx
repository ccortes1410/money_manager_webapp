import React, { useState, useEffect } from 'react';
import './Budgets.css'

const BudgetBar = ({ budget, onDelete, onSelect }) => {
    // const { name, total, spent, members = [] } = budget;
    // const [transactions, setTransactions] = useState([]);
    // const [spent, setSpent] = useState(0);

    const spentPct = budget.amount ? (budget.spent/budget.amount) * 100 : 0;
    const overBudget = budget.spent > budget.amount;
    const remainingPct = Math.max(100 - spentPct, 0);
    console.log(overBudget)
    return (
        <div className='budget-bar' onClick={() => onSelect && onSelect(budget)}>
            <div className='budget-info'>
                <span>{budget.name}</span>
                <span>
                    ${budget.amount}
                </span>
            </div>
        
        {/* Single-user / My Budget bar */}
        
        {/* {!shared && ( */}
        <div className="bar-row">
            <button 
                className="delete-budget-button"
                onClick={(e) => {
                e.stopPropagation();
                onDelete && onDelete(budget.id);
                }}
                >
                    -
                </button>
            <div className="progress-bar dual">
                <div
                    className='progress-fill remaining'
                    style={{ width: `${remainingPct}%`}}
                ></div>

                <div
                    className={`progress-fill spent ${overBudget ? "over" : ""}`}
                    style={{ width: `${spentPct}%` }}
                ></div>
            </div>
        </div>
        {/* )} */}

        {/* Shared budget bar (each member color)
        {shared && (
            <div className='progress-bar shared'>
                {members.map((m) => (
                    <div
                        key={m.id}
                        className='progress-fill'
                        style={{
                            width: `${(m.spent / total) * 100}%`,
                            backgroundColor: m.color ||  "#17a2b8",
                        }}
                        title={`${m.name}: $${m.spent.toFixed(2)}`}
                        ></div>
        ))}
        </div>
        )} */}
    </div>
    );
};

export default BudgetBar;