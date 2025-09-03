import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../Dashboard/Dashboard.css';
import Sidebar from '../Sidebar/Sidebar';
import Budget from './Budget';

const Budgets = () => {
    const [collapsed, setCollapsed] = useState(true);
    const [budgets, setBudgets] = useState([]);
    // const [budget, setBudget] = useState(null);
    const [selectedBudgetId, setSelectedBudgetId] = useState('');
    const [user, setUser] = useState(null);

    const budgets_url = '/djangoapp/budgets';
    const navigate = useNavigate();

    const get_budgets = async () => {
        try {
            const response = await fetch(budgets_url, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.budgets && Array.isArray(data.budgets)) {
                setBudgets(data.budgets);
                if (data.budgets.length > 0) {
                    setSelectedBudgetId(data.budgets[0].id);
                }
            }
        } catch (error) {
            alert('Error fetching budgets');
            setBudgets([]);
            console.error(error);
        }
    }

    useEffect(() => {
        get_budgets();
    }, []);

    // useEffect(() => {
    //     if (selectedBudgetId) {
    //         get_budget(selectedBudgetId);
    //     }
    // }, [selectedBudgetId]);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/');
        }
    }, [user]); 

    return (
        <div style={{ display: 'flex', width: '100vw', minHeight: '100vh' }}>
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
            <div className="budget-container">
                <h2>Budget</h2>
                <table className="budget-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Amount</th>
                            <th>Period</th>
                        </tr>
                    </thead>
                        <tbody>
                            {budgets.length > 0 ? (
                                budgets.map((item) => (
                                    <tr key={item.id}>
                                    <td>{item.name}</td>
                                    <td>${item.amount}</td>
                                    <td>{item.period}</td>
                                </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="4">No budget data available</td>
                                </tr>
                            )}
                        </tbody>
                    <tfoot>
                        <tr>
                            <td colSpan="2">Total Budget</td>
                            <td>${budgets.reduce((acc, item) => acc + Number(item.amount), 0)}</td>
                        </tr>
                    </tfoot>
                </table>
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
                <p>Your current budget is: ${budgets.reduce((acc, item) => acc + Number(item.amount), 0)}</p>
            </div>
            {selectedBudgetId && <Budget selectedBudgetId={selectedBudgetId} />}
        </div>
    );
}

export default Budgets;
