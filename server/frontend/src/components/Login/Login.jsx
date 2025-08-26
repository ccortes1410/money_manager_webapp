import React, { useState } from 'react';

import './Login.css';
import Header from '../Sidebar/Sidebar';
import Sidebar from '../Sidebar/Sidebar';

const Login = ({ onClose }) => {

    const [userName, setUserName] = useState('');
    const [password, setPassword] = useState('');
    const [open, setOpen] = useState(true);

    let login_url = window.location.origin + "/djangoapp/login";

    const login = async (e) => {
        e.preventDefault();

        const res = await fetch(login_url, {
            method: 'POST',
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                userName: userName,
                password: password
            })
    });

    const json = await res.json();
    if (json.status != null && json.status === "Authenticated") {
        sessionStorage.setItem('username', json.userName);
        setOpen(false);
    }
    else {
        alert("The user could not be authenticated");
    }
    };

    if (!open) {
        window.location.href = '/dashboard';
    }

    return (
        <div>
            <Sidebar/>
        <div onClick={onClose}>
            <div    
                onClick={(e) => {
                e.stopPropagation();
            }}
            className='modalContainer'
            >
                <form className="login_panel" style={{}} onSubmit={login}>
                    <div>
                        <span className="input_field">Username</span>
                        <input
                            type="text"
                            placeholder="Username"
                            name="username"
                            className="input_field"
                            value={userName}
                            onChange={(e) => setUserName(e.target.value)}
                        />
                    </div>
                    <div>
                        <span className="input_field">Password</span>
                        <input
                            type="password"
                            placeholder="Password"
                            name="psw"
                            className="input_field"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                    <div>
                    <input className="action_button" type="submit" value="Login"/>
                    <input className="action_button" type="button" value="Cancel" onClick={()=>setOpen(false)}/>
                    </div>
                    <a className="loginlink" href="/register">Register Now</a>
                </form>
            </div>
        </div>
        </div>
    )

};

export default Login;