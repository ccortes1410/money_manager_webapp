import Login from './components/Login/Login';
import { Routes, Route } from 'react-router-dom';
import Register from './components/Register/Register';
import Dashboard from './components/Dashboard/Dashboard';
import Budget from './components/Budgets/Budget';
import Budgets from './components/Budgets/Budgets';
import AddBudget from './components/Budgets/AddBudget';

function App() {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/budgets" element={<Budgets />} />
            <Route path="/budget/:budget_id" element={<Budget />} />
            <Route path="/add-budget" element={<AddBudget />} />
        </Routes>
    );
}

export default App;