import React, { useState } from 'react';
import './Register.css';
import user_icon from '../assets/person.png';
import email_icon from '../assets/email.png';
import password_icon from '../assets/password.png';
import close_icon from '../assets/close.png';

const Register = () => {
    const [userName, setUserName] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');

    const gohome = () => {
        window.location.href = window.location.origin;
    }

    const register = async (e) => {
        e.preventDefault();

        let register_url = "/djangoapp/register";

        const res = await fetch(register_url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "username": userName,
                "password": password,
                "email": email,
                "first_name": firstName,
                "last_name": lastName
            })
        });

        const json = await res.json();
        if (json.status) {
            // Save username in session a reload home
            sessionStorage.setItem('username', json.userName);
            window.location.href = window.location.origin;
        }
        else if (json.error == "Already Registered") {
            alert("The user with same username is already registered");
            window.location.href = window.location.origin;
        }
    };

    return (
        <div className="register-container">
            <div className="register-header">
                <span className='register-span'>Sign Up</span>
                <div className="register-exit">
                    <a href="/" onClick={()=>{gohome()}} style={{justifyContent: "space-between", alignItems: "flex-end"}}>
                        <img src={close_icon} alt="X" style={{width: "1cm", borderRadius: "50%"}}/>
                    </a>
                </div>
                <hr/>
            </div>
           <form onSubmit={register}>
                <div className="register-inputs">
                    <div className="register-input">
                        <img src={user_icon} className="img_icon_reg" alt="Username"/>
                        <input type="text" name="username" placeholder="Username" className="input_field" onChange={(e) => {setUserName(e.target.value)}}/>
                    </div>
                    <div className="register-input">
                        <img src={user_icon} className="img_icon_reg" alt="First Name"/>
                        <input type="text" name="first_name" placeholder="First Name" className="input_field" onChange={(e) => {setFirstName(e.target.value)}}/>
                    </div>
                    <div className="register-input">
                        <img src={user_icon} className="img_icon_reg" alt="Last Name"/>
                        <input type="text" name="last_name" placeholder="Last Name" className="input_field" onChange={(e) => {setLastName(e.target.value)}}/>
                    </div>
                    <div className="register-input">
                        <img src={email_icon} className="img_icon_reg" alt="Email"/>
                        <input type="email" name="email" placeholder="Email" className="input_field" onChange={(e) => {setEmail(e.target.value)}}/>
                    </div>
                    <div className="register-input">
                        <img src={password_icon} className="img_icon_reg" alt="Password"/>
                        <input type="password" name="psw" placeholder="Password" className="input_field" onChange={(e) => {setPassword(e.target.value)}}/>
                    </div>
                </div>
                <div className="submit-panel">
                    <input className="submit-btn" type="submit" value="Register"/>
                </div>
            </form> 
        </div>
    )
}

export default Register;