import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../Dashboard/Dashboard.css';
import Sidebar from '../Sidebar/Sidebar';

const Budget = () => {
    const [collapsed, setCollapsed] = useState(true);
    const [budgets, setBudgets] = useState([]);
    // const [budget, setBudget] = useState(null);
    const [selectedBudgetId, setSelectedBudgetId] = useState('');
    const [user, setUser] = useState(null);

    const budget_url = 'djangoapp/budget';
    const navigate = useNavigate();

    const get_budgets = async () => {
        try {
            const response = await fetch(budget_url, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();
            setBudgets(data);
            if (data.length > 0) {
                setSelectedBudgetId(data[0].id);
            }
        } catch (error) {
            alert('Error fetching budget');
            console.error(error);
        }
    }

    const get_budget = async (budgetId) => {
        try {
            const response = await fetch(`${budget_url}/${budgetId}`, {
                method: 'GET',
                credentials: 'include'
            });
            const data = await response.json();
            setBudgets(data[budgetId]);
        } catch (error) {
            alert('Error fetching budget');
            console.error(error);
        }
    };

    useEffect(() => {
        get_budgets();
    }, []);

    useEffect(() => {
        if (selectedBudgetId) {
            get_budget(selectedBudgetId);
        }
    }, [selectedBudgetId]);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/');
        }
    }, [user]); 

    return (
        <div style={{ display: 'flex', width: '100vw', minHeight: '100vh' }}>
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
            <div className="budget-container">
                <div>
                    <select
                        value={selectedBudgetId}
                        onChange={(e) => setSelectedBudgetId(e.target.value)}
                        style={{ margin: '20px' }}
                    >
                        {budgets.map((budget) => (
                            <option key={budget.id} value={budget.id}>
                                {budget.name}
                            </option>
                        ))}
                    </select>
                </div>
                <table className="budget-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Description</th>
                            <th>Amount</th>
                            <th>Period</th>
                        </tr>
                    </thead>
                    {budgets ? (
                        <tbody>
                            {budgets.map((item) => (
                                <tr key={item.id}>
                                    <td>{item.name}</td>
                                    <td>{item.description}</td>
                                    <td>${item.amount}</td>
                                    <td>{item.period}</td>
                                </tr>
                            ))}
                        </tbody>
                    ) : (
                        <tbody>
                            <tr>
                                <td colSpan="4">No budget data available</td>
                            </tr>
                        </tbody>
                    )}
                    <tfoot>
                        <tr>
                            <td colSpan="2">Total Budget</td>
                            <td>${budgets.reduce((acc, item) => acc + item.amount, 0)}</td>
                            <td></td>
                        </tr>
                    </tfoot>
                </table>
                <h2>Budget</h2>
                <p>Your current budget is: ${budgets.reduce((acc, item) => acc + item.amount, 0)}</p>
            </div>
        </div>
    );
}

export default Budget;
