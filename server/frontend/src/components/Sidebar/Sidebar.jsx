import React, { useState } from 'react';
import "../assets/style.css";
import "../assets/bootstrap.min.css";

const Sidebar = () => {
    const [collapsed, setCollapsed] = useState(true);

    const toggleSidebar = () => {
        setCollapsed(!collapsed);
    }

    const logout = async (e) => {
        e.preventDefault();
        let logout_url = window.location.origin + "/djangoapp/logout";
        const res = await fetch(logout_url, {
            method: 'GET',
        });

        const json = await res.json();
        if (json) {
            let username = sessionStorage.getItem('username');
            sessionStorage.removeItem('username');
            window.location.href = window.location.origin;
            window.location.reload();
            alert("Logging out " + username + "...")
        }
        else {
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
            className="d-flex flex-column flex-shrink-0 p-3 bg-light" 
            style={{
                width: '250px', 
                height: '100vh', 
                position: 'fixed',
                transition: 'width 0.3s'
                }}
        >
            <button
                className="btn btn-outline-secondary"
                onClick={toggleSidebar}
                aria-label="Toggle Sidebar"
            >
                {collapsed ? '→' : '←'}
            </button>
            <a href="/" className="d-flex align-items-center mb-3 mb-md-0 me-md-auto link-dark tex-decoration-none">
                {!collapsed && <span className="fs-4">Money Manager</span>}
            </a>
            <hr/>
            <ul className="nav nav-pills flex-column mb-auto">
                <li className="nav-item">
                    {collapsed ? <a className="nav-link active" aria-current="page" href="/">
                    <img src="hogar.png" className="img_icon"/>
                    </a> : <span className="nav-link active">Home</span>}
                </li>
                <li className="nav-item">
                    {collapsed ? <a className="nav-link" href="/profile"><img src="persona.png" className="img_icon"/></a> : <span className="nav-link">Profile</span>}
                </li>
                <li className="nav-item">
                    {collapsed ? <a className="nav-link" href="/friends"><img src="friends.png" className="img_icon"/></a> : <span className="nav-link">Friends</span>}
                </li>
            </ul>
            <hr/>
            <div>
                <a className="nav-link" href="/logout">Logout</a>
            </div>
        </div>
    )
}

export default Sidebar;