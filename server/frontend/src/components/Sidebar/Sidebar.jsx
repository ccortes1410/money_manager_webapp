import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import "../assets/bootstrap.min.css";
import "../assets/style.css";
import "../Dashboard/Dashboard.css"
import dashIcon from '../assets/panel.png';
import budgetIcon from '../assets/budget.png';
import friendsIcon from '../assets/amigos.png';
import logoutIcon from '../assets/salida.png';

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
            <a href="/" className="d-flex align-items-center mb-3 mb-md-0 me-md-auto link-dark tex-decoration-none">
                {!collapsed && <span className="fs-4">Money Manager</span>}
            </a>
            <hr/>
            <ul className="nav flex-column mb-auto">
                <li className={`nav-item${currentPath === '/dashboard' ? ' active' : ''}`}>
                    {collapsed ? (
                        <a 
                            className={`nav-link`}
                            aria-current="page"
                            href="/dashboard"
                        >
                            <img 
                                src={dashIcon}
                                style={{ 
                                        width: '30px',
                                        height: '30px',
                                        alignContent: 'center',
                                        objectFit: 'contain'
                                        }}
                                className="img_icon"/>
                        </a>
                    ) : (
                        <a
                            className="nav-link"
                            href="/dashboard"
                            style={{
                                marginLeft: '20px',
                                }}
                        >
                            Dashboard
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
                                style={{ 
                                    width: '30px',
                                    height: '30px',
                                    alignContent: 'center',
                                    objectFit: 'contain'
                                    }}
                                className="img_icon"
                            />
                        </a>
                    ) : (
                        <a
                            className="nav-link"
                            href="/budgets"
                        >
                            Budgets
                        </a>
                    )}
                </li>
                <li className={`nav-item${currentPath === '/friends' ? ' active' : ''}`}>
                    {collapsed ? (
                        <a className={`nav-link`} href="/friends">
                            <img 
                                src={friendsIcon}
                                style={{
                                    width: '30px',
                                    height: '30px',
                                    alignContent: 'center',
                                    objectFit: 'contain'
                                    }}
                                className="img_icon"/>
                        </a>
                    ) : (
                        <a 
                            className="nav-link"
                        >
                            Friends
                        </a>
                    )}
                </li>
            </ul>
            <hr/>
            <div>
                {collapsed ? (
                    <a className="nav-link" href="#" onClick={logout}>
                        <img src={logoutIcon} style={{ width: '24px', height: '24px' }} className="img_icon"/>
                    </a>
                ) : (
                    <a className="nav-link" href="#" onClick={logout}>Logout</a>
                )}
            </div>
        </div>
    )
}

export default Sidebar;