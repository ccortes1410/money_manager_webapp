import React, { useEffect, useNavigate } from 'react';
import '../Dashboard/Dashboard.css';
import Sidebar from '../Sidebar/Sidebar';

const Budget = () => {
    const [collapsed, setCollapsed] = React.useState(true);
    const [budget, setBudget] = React.useState(0);

    const budget_url = '/budget';
    const navigate = useNavigate();

    const get_budget = async () => {
        try {
            const response = await fetch(budget_url, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();
            setBudget(data.budget);
        } catch (error) {
            alert('Error fetching budget');
            console.error(error);
        }
    }



    return (
        <div style={{ display: 'flex', width: '100vw', minHeight: '100vh' }}>
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
            <div className="budget-container">
                <table className="budget-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Description</th>
                            <th>Amount</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {}
                    </tbody>
                </table>
                <h2>Budget</h2>
                <p>Your current budget is: ${budget}</p>
            </div>
        </div>
    );
}
