import React, { useContext } from 'react';
import { useLocation, useNavigate, NavLink } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import "../Sidebar/Sidebar.css";

import travelIcon from '../assets/travel.png';
import budgetIcon from '../assets/budget.png';
import detailIcon from '../assets/detail.png';
import logoutIcon from '../assets/salida.png';
import homeIcon from '../assets/home.png';
import subscriptionIcon from '../assets/subscription.png';
import bankIcon from '../assets/bank.png';
import friendIcon from '../assets/friend.png';
import incomeIcon from '../assets/income.png';

const Sidebar = ({ collapsed, onToggle }) => {
    const { user, setUser } = useContext(AuthContext);
    const location = useLocation();
    const navigate = useNavigate();

    const navItems = [
        { path: "/dashboard", label: "Dashboard", icon: homeIcon },
        { path: "/transactions", label: "Transactions", icon: detailIcon },
        { path: "/budgets", label: "Budgets", icon: budgetIcon },
        { path: "/subscriptions", label: "Subscriptions", icon: subscriptionIcon },
        { path: "/income", label: "Income", icon: incomeIcon},
        { path: "/friends", label: "Friends", icon: friendIcon},
    ];

    const isActive = (path) => {
        return location.pathname === path || location.pathname === `${path}/`;
    };

    const logout = async (e) => {
        e.preventDefault();
        const logout_url = window.location.origin + "/djangoapp/logout";

        try {
            const res = await fetch(logout_url, {
                method: 'GET',
                credentials: 'include'
            });

            const json = await res.json();
            if (json && json.status === "logged_out") {
                const username = user ? user.username : "";
                alert(`Logging out ${username}...`)
                setUser(null);
                navigate("/login")
            } else {
                alert("The user could not be logged out");
            }
        } catch (error) {
            console.error("The user could not be logged out");
            alert("An error ocurred during logout")
        }
    }

    if (!user) return null;

    return (

        <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
            {/* Collapse Toggle Button */}
            <div className="collapse-btn-container">
                <button
                className="collapse-btn"
                onClick={onToggle}
            >
                {collapsed ? '>' : '<'}
            </button>
            </div>
            {/* Logo / Header */}
            <NavLink to="/" className="sidebar-header">
                <div className="sidebar-logo">
                    <div className="sidebar-logo-icon">💰</div>
                    <span className="sidebar-logo-text">Money Manager</span>
                </div>
            </NavLink>

            {/* Main Navigation */}
            
            <ul className="nav-links">
                {navItems.map((item) => (
                    <li
                        key={item.path}
                        className="nav-item"
                        data-tooltip={item.label}
                    >
                        <NavLink
                            to={item.path}
                            className={`nav-link ${isActive(item.path) ? "active" : ""}`}
                        >
                            <span className="nav-icon">
                                <img src={item.icon} alt={item.label} className="img_icon" />
                            </span>
                            <span className="nav-text">{item.label}</span>
                        </NavLink>
                    </li>
                ))}
            </ul>
            
            {/* User Section */}
            {user && (
                <div className="sidebar-user">
                    <div className="user-avatar">
                        {user.userName?.charAt(0).toUpperCase() || "U"}
                    </div>
                    <div className="user-info">
                        <span className="user-name">{user.username}</span>
                        <span className="user-email">{user.email || "User"}</span>
                    </div>
                </div>
            )}

            {/* Logout */}
            <ul className="nav-links logout">
                <li className="nav-item" data-tooltip="Logout">
                    <NavLink
                        to="/"
                        className="nav-link"
                        onClick={logout}
                    >
                        <span className="nav-icon">
                            <img src={logoutIcon} alt="Logout" className="img_icon" />
                        </span>
                        <span className="nav-text">Logout</span>
                    </NavLink>
                </li>
            </ul>
        </aside>
    );
};

export default Sidebar;