import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import "../assets/bootstrap.min.css";
import "../assets/style.css";
import "../Dashboard/Dashboard.css"
import "../Sidebar/Sidebar.css";
// import dashIcon from '../assets/panel.png';
import budgetIcon from '../assets/budget.png';
import detailIcon from '../assets/detail.png';
import logoutIcon from '../assets/salida.png';
import homeIcon from '../assets/home.png';
import subscriptionIcon from '../assets/subscription.png';
import bankIcon from '../assets/bank.png';
import friendIcon from '../assets/friend.png';

const Sidebar = ({ collapsed, setCollapsed }) => {
    const location = useLocation();
    const currentPath = location.pathname;

    const toggleSidebar = () => {
        setCollapsed(!collapsed);
    }

    const logout = async (e) => {
        e.preventDefault();
        let logout_url = window.location.origin + "/djangoapp/logout";
        const res = await fetch(logout_url, {
            method: 'GET',
            credentials: 'include'
        });

        const json = await res.json();
        if (json && json.status === "logged_out") {
            let username = sessionStorage.getItem('username');
            sessionStorage.removeItem('username');
            alert("Logging out " + username + "...")
            window.location.href = "/login";
        } else {
            alert("The user could not be logged out");
        }
    }

    let home_page_items = <div></div>;

    let curr_user = sessionStorage.getItem('username');

    if ( curr_user !== null && curr_user !== "") {
        home_page_items = <div className="input_panel">
            <text className='username'>{sessionStorage.getItem("username")}</text>
            <a className="nav_item" href="/djangoapp/logout" onClick={logout}>Logout</a>
        </div>
    }

    return (
        <div 
            className={collapsed ? 'sidebar' : 'sidebar expanded'}
        >
            <button
                className="btn btn-outline-secondary mb-3"
                style={{ width: '100%' }}
                onClick={toggleSidebar}
                aria-label="Toggle Sidebar"
            >
                {collapsed ? '→' : '←'}
            </button>
            <a href="/" className="sidebar-header">
                {!collapsed && <span className="fs-4">Money Manager</span>}
            </a>
            <hr/>
            <ul className="nav flex-column mb-auto" style={{ alignItems: 'center' }} >
                <li className={`nav-item${currentPath === '/dashboard' ? ' active' : ''}`}>
                    {collapsed ? (
                        <a 
                            className={`nav-link`}
                            aria-current="page"
                            href="/dashboard"
                        >
                            <img 
                                src={homeIcon}
                                className="img_icon"/>
                        </a>
                    ) : (
                        <a
                            className="sidebar-link"
                            href="/dashboard"
                        >  
                            Dashboard
                        </a>
                    )}
                </li>
                <li className={`nav-item${currentPath === '/transactions' ? ' active' : ''}`}>
                    {collapsed ? (
                        <a
                            className={`nav-link`}
                            href="/transactions"
                        >
                            <img 
                                src={detailIcon}
                                className="img_icon"/>
                        </a>
                    ) : (
                        <a
                            className="sidebar-link"
                            href="/transactions"
                        >
                            Transactions
                        </a>
                    )}
                </li>
                <li className={`nav-item${currentPath === '/budgets' ? ' active' : ''}`}>
                    {collapsed ? (
                        <a 
                            className="nav-link"
                            href="/budgets"
                        >
                            <img 
                                src={budgetIcon}
                                className="img_icon"
                            />
                        </a>
                    ) : (
                        <a
                            className="sidebar-link"
                            href="/budgets"
                        >
                            Budgets
                        </a>
                    )}
                </li>
                <li className={`nav-item${currentPath === '/subscriptions' ? ' active' : ''}`}>
                    {collapsed ? (
                        <a 
                            className={`nav-link`}
                            href="/subscriptions"
                        >
                            <img 
                                src={subscriptionIcon}
                                className="img_icon"
                            />
                        </a>
                    ) : (
                        <a
                            className="sidebar-link"
                            href="/subscriptions"
                        >
                            Subscriptions
                        </a>
                    )}
                </li>
                <li className={`nav-item${currentPath === '/savings' ? ' active' : ''}`}>
                    {collapsed ? (
                        <a className={`nav-link`} href="/savings">
                            <img 
                                src={bankIcon}
                                className="img_icon"
                            />
                        </a>
                    ) : (
                        <a
                            className="sidebar-link"
                            href="/savings"
                        >
                            Savings
                        </a>
                    )}
                </li>
                <li className={`nav-item${currentPath === '/friends' ? ' active' : ''}`}>
                    {collapsed ? (
                        <a className={`nav-link`} href="/friends">
                            <img 
                                src={friendIcon}
                                className="img_icon"/>
                        </a>
                    ) : (
                        <a 
                            className="sidebar-link"
                            href="/friends"
                        >
                            Friends
                        </a>
                    )}
                </li>
            </ul>
            <hr/>
            <div>
                {collapsed ? (
                    <a className="sidebar-link" href="/" onClick={logout}>
                        <img src={logoutIcon} style={{ width: '24px', height: '24px' }} className="img_icon"/>
                    </a>
                ) : (
                    <a className="sidebar-link" href="/" onClick={logout}>Logout</a>
                )}
            </div>
        </div>
    )
}

export default Sidebar;