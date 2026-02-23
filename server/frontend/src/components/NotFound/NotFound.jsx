import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './NotFound.css';

const NotFound = () => {
    const navigate = useNavigate();

    return (
        <div className="not-found-page">
            <div className="nf-bg">
                <div className="nf-glow" />
            </div>

            <div className="not-found-content">
                <span className="nf-code">404</span>
                <h1>Page not found</h1>
                <p>
                    The page you are looking for doesn't exist or has been moved.
                </p>
                <div className="nf-actions">
                    <button
                        className="nf-btn-primary"
                        onClick={() => navigate("/")}
                    >
                        🏠 Go Home
                    </button>
                    <button
                        className="nf-btn-secondary"
                        onClick={() => navigate(-1)}
                    >
                        ← Go Back
                    </button>
                </div>
                <div className="nf-links">
                    <Link to="/dashboard">Dashboard</Link>
                    <span>•</span>
                    <Link to="/transactions">Transactions</Link>
                    <span>•</span>
                    <Link to="/budgets">Budgets</Link>
                    <span>•</span>
                    <Link to="/subscriptions">Subscriptions</Link>
                    <span>•</span>
                    <Link to="/income">Income</Link>
                    <span>•</span>
                    <Link to="/shared-budgets">Shared Budgets</Link>
                    <span>•</span>
                </div>
            </div>
        </div>
    );
};

export default NotFound;