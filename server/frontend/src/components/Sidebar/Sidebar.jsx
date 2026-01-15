import React, { useContext } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { NavLink } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import "../assets/bootstrap.min.css";
import "../assets/style.css";
import "../Dashboard/Dashboard.css"
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
    const currentPath = location.pathname;
    const navigate = useNavigate();
    // const toggleSidebar = () => {
    //     setCollapsed(!collapsed);
    // }

    const logout = async (e) => {
        e.preventDefault();
        let logout_url = window.location.origin + "/djangoapp/logout";
        const res = await fetch(logout_url, {
            method: 'GET',
            credentials: 'include'
        });

        const json = await res.json();
        if (json && json.status === "logged_out") {
            let username = user ? user.username : "";
            // let username = sessionStorage.getItem('username');
            alert("Logging out " + username + "...")
            setUser(null);
            navigate("/login")
        } else {
            alert("The user could not be logged out");
        }
    }

    if (!user) return null;

    // let home_page_items = <div></div>;

    // let curr_user = sessionStorage.getItem('username');

    // if ( curr_user !== null && curr_user !== "") {
    //     home_page_items = <div className="input_panel">
    //         <text className='username'>{sessionStorage.getItem("username")}</text>
    //         <a className="nav_item" href="/djangoapp/logout" onClick={logout}>Logout</a>
    //     </div>
    // }
    return (

        <aside 
            className={`sidebar ${collapsed ? "collapsed" : ""}`}>
            <button
                className="collapse-btn"
                onClick={onToggle}
            >
                {collapsed ? '>' : '<'}
            </button>

            <a href="/" className="sidebar-header">
                {!collapsed && <span className="fs-4">Money Manager</span>}
            </a>
            <hr/>
            <nav className={`nav-links ${collapsed ? "collapsed" : ""}`}>
                <li className={`nav-item ${currentPath === '/dashboard' ? 'active' : ''} ${collapsed ? 'collapsed': ''}`}>
                    {collapsed ? (
                        <NavLink 
                            to="/dashboard"
                            className={({isActive}) => `nav-link ${isActive || currentPath === '/dashboard' ? 'active' : ''}`}
                            aria-current="page"
                        >
                            <img 
                                src={homeIcon}
                                className="img_icon"/>
                        </NavLink>
                    ) : (
                        <NavLink
                            className={({isActive}) => `sidebar-link ${isActive || currentPath === '/dashboard' ? 'active' : ''}`}
                            to="/dashboard"
                        >  
                            Dashboard
                        </NavLink>
                    )}
                </li>
                <li className={`nav-item ${currentPath === '/transactions' ? 'active' : ''} ${collapsed ? 'collapsed': ''}`}>
                    {collapsed ? (
                        <NavLink
                            className={({isActive}) => `nav-link ${isActive || currentPath === '/transactions' ? 'active' : ''}`}
                            to="/transactions"
                        >
                            <img 
                                src={detailIcon}
                                className="img_icon"
                            />
                        </NavLink>
                    ) : (
                        <NavLink
                            className={({isActive}) => `sidebar-link ${isActive || currentPath === '/transactions' ? 'active' : ''}`}
                            to="/transactions"
                        >
                            Transactions
                        </NavLink>
                    )}
                </li>
                <li className={`nav-item ${currentPath === '/budgets' ? 'active' : ''} ${collapsed ? 'collapsed': ''}`}>
                    {collapsed ? (
                        <NavLink 
                            className={({isActive}) => `nav-link ${isActive || currentPath === '/budgets' ? 'active' : ''}`}
                            to="/budgets"
                        >
                            <img 
                                src={budgetIcon}
                                className="img_icon"
                            />
                        </NavLink>
                    ) : (
                        <NavLink
                            className={({isActive}) => `sidebar-link ${isActive || currentPath === '/budgets' ? 'active' : ''}`}
                            to="/budgets"
                        >
                            Budgets
                        </NavLink>
                    )}
                </li>
                <li className={`nav-item ${currentPath === '/subscriptions' ? 'active' : ''} ${collapsed ? 'collapsed': ''}`}>
                    {collapsed ? (
                        <NavLink 
                            className={({isActive}) => `nav-link ${isActive || currentPath === '/subscriptions' ? 'active' : ''}`}
                            to="/subscriptions"
                        >
                            <img 
                                src={subscriptionIcon}
                                className="img_icon"
                            />
                        </NavLink>
                    ) : (
                        <NavLink
                            className={({isActive}) => `sidebar-link ${isActive || currentPath === '/subscriptions' ? 'active' : ''}`}
                            to="/subscriptions"
                        >
                            Subscriptions
                        </NavLink>
                    )}
                </li>
                <li className={`nav-item ${currentPath === '/income' ? 'active' : ''} ${collapsed ? 'collapsed': ''}`}>
                    {collapsed ? (
                        <NavLink 
                            className={({isActive}) => `nav-link ${isActive || currentPath === '/income' ? 'active' : ''}`}
                            to="/income"
                            end
                        >
                            <img 
                                src={incomeIcon}
                                className="img_icon"
                            />
                        </NavLink>
                    ) : (
                        <NavLink
                            className={({isActive}) => `sidebar-link ${isActive || currentPath === '/income' ? 'active' : ''}`}
                            to="/income"
                        >
                            Income
                        </NavLink>
                    )}
                </li>
                {/* <li className={`nav-item${currentPath === '/income' ? ' active' : ''}`}>
                    {collapsed ? (
                        <a className={`nav-link`} href="/income">
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
                </li> */}
            </nav>
            <hr/>
            <nav className={`nav-links logout ${collapsed ? 'collapsed' : ''}`}>
                {collapsed ? (
                    <NavLink 
                        className={({isActive}) => `nav-link ${isActive || currentPath === '/' ? 'active' : ''}`}
                        to="/"
                        onClick={logout}
                    >
                        <img 
                            src={logoutIcon}
                            className="img_icon"
                        />
                    </NavLink>
                ) : (
                    <NavLink 
                        className={(isActive) => `sidebar-link ${isActive || currentPath === '/' ? 'active' : ''}`}
                        to="/" 
                        onClick={logout}
                    >
                        Logout
                    </NavLink>
                )}
            </nav>
        </aside>
    )
}

export default Sidebar;