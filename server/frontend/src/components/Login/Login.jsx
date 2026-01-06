import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';
import Header from '../Sidebar/Sidebar';
import Sidebar from '../Sidebar/Sidebar';

const Login = () => {
    const [collapsed, setCollapsed] = useState(true);
    const [userName, setUserName] = useState('');
    const [password, setPassword] = useState('');
    // const [open, setOpen] = useState(true);

    let login_url ="/djangoapp/login";

    const navigate = useNavigate();

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
            }),
            credentials: 'include',
        });

        const json = await res.json();
        if (json.status != null && json.status === "Authenticated") {
            sessionStorage.setItem('username', json.userName);
            // setOpen(false);
            navigate('/dashboard');
        }
        else {
            alert("The user could not be authenticated");
        }
    };

    return (
        // <div style={{ display: 'flex', width: '100vw', minHeight: '100vh' }}>
        //     <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
        <div>
            <div
                onClick={(e) => {
                e.stopPropagation();
            }}
            className='modalContainer'
            >
                <form className="login_panel" onSubmit={login}>
                    <div>
                        {/* <span className="input_field">Username</span> */}
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
                        {/* <span className="input_field">Password</span> */}
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
                    <input className="action_button" type="button" value="Cancel" onClick={() => navigate('/home')}/>
                    </div>
                    {/* <a className="loginlink" href="/register">Register Now</a> */}
                </form>
            </div>
        </div>
        // </div>
    )

};

export default Login;