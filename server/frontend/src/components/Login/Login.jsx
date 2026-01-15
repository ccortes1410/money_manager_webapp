import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import './Login.css';

const Login = () => {
    const [userName, setUserName] = useState('');
    const [password, setPassword] = useState('');
    const { user, setUser } = useContext(AuthContext);
    const navigate = useNavigate();
    let login_url ="/djangoapp/login";

    const login = async (e) => {
        e.preventDefault();

        const res = await fetch(login_url, {
            method: 'POST',
            credentials: 'include',
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                username: userName,
                password: password
            }),
        });
        console.log(res);
        if (res.ok) {
            const user = await res.json();
            // sessionStorage.setItem('username', user.username);
            setUser(user);
            navigate('/dashboard')
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
                            name="userName"
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
                    <input className="action_button" type="button" value="Cancel" onClick={() => navigate('/')}/>
                    </div>
                    {/* <a className="loginlink" href="/register">Register Now</a> */}
                </form>
            </div>
        </div>
        // </div>
    )

};

export default Login;