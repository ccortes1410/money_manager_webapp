import Login from './components/Login/Login';
import { Routes, Route } from 'react-router-dom';
import Register from './components/Register/Register';
import Dashboard from './components/Dashboard/Dashboard';

function App() {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
    );
}

export default App;