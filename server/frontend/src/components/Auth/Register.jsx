import React, { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import { useToast } from '../Toast/ToastContext';
import { apiFetch } from '../../utils/csrf';
import { sanitizeInput, isValidEmail } from '../../utils/sanitize';
import './Login.css';

const Register = () => {
    const [ userName, setUserName ] = useState('');
    const [ password, setPassword ] = useState('');
    const [ confirmPassword, setConfirmPassword ] = useState('');
    const [ email, setEmail ] = useState('');
    const [ firstName, setFirstName ] = useState('');
    const [ lastName, setLastName ] = useState('');
    const [ error, setError ] = useState('');
    const [ fieldErrors, setFieldErrors ] = useState({});
    const [ loading, setLoading ] = useState(false);

    const { setUser } = useContext(AuthContext);
    const navigate = useNavigate();
    const toast = useToast();

    const register_url = "/djangoapp/register";

    const validate = () => {
        const errors = {};
        if (!userName.trim()) errors.username = 'Username is required';
        if (!firstName.trim()) errors.firsstName = 'First Name is required';
        if (!lastName.trim()) errors.lastName = 'Last name is required';
        if (!email.trim()) {
            errors.email = 'Email is required';
        } else if (isValidEmail(email)) {
            errors.email = 'Please enter a valid email';
        }
        if (!password) {
            errors.password = 'Password is required';
        } else if (password.length < 8) {
            errors.password = 'Password must be at least 8 characters'
        }
        if (password !== confirmPassword) {
            errors.confirmPassword = 'Passwords do not match';
        }
        setFieldErrors(errors);
        return Object.keys(errors).length = 0;
    };

    const register = async (e) => {
        e.preventDefault();
        setError('');

        if (!validate()) return;

        setLoading(true);

        try {
            const res = await fetch(register_url, {
                method: 'POST',
                body: JSON.stringify({
                    username: sanitizeInput(userName),
                    password: password,
                    email: sanitizeInput(email),
                    first_name: sanitizeInput(firstName),
                    last_name: sanitizeInput(lastName),
                })
            });

            const json = await res.json();

            if (json.status) {
                setUser({
                    username: json.userName,
                    is_authenticated: true,
                });
                toast.success("Account created! Welcome to Money Manager 🎉")
                navigate('/dashboard');
            } else if (json.error === "Already Registered") {
                setError('An account with that username already exists. Please try a different one.');
            } else {
                setError('Registration failed. Please try again.');
            }
        } catch (error) {
            console.error("Registration error:", error);
            setError('Something went wrong. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    const clearFieldError = (field) => {
        if (fieldErrors[field]) {
            setFieldErrors(prev => ({ ...prev, [field]: '' }));
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-bg">
                <div className="auth-glow glow-1"/>
                <div className="auth-glow glow-2"/>
            </div>

            <div className="auth-container" style={{ maxWidth: '500px' }}>
                {/* Branding */}
                <Link to="/" className="auth-logo">
                    <span className="auth-logo-icon">💰</span>
                    <span className="auth-logo-text">Money Manager</span>
                </Link>

                {/* Card */}
                <div className="auth-card">
                    <div className="auth-card-header">
                        <h1>Create your account</h1>
                        <p>Start managing your finances in under a minute</p>
                    </div>

                    {error && (
                        <div className="auth-error">
                            <span className="auth-error-icon">⚠️</span>
                            {error}
                        </div>
                    )}

                    <form onSubmit={register} className="auth-form">
                        {/* First & Last Name - Side by Side */}
                        <div className="auth-form-row">
                            <div className="auth-form-group">
                                <label htmlFor="firstName">First Name</label>
                                <div className={`auth-input-wrapper ${fieldErrors.firstName ? 'error' : ''}`}>
                                    <span className="auth-input-icon">👤</span>
                                    <input
                                        type="text"
                                        id="firstName"
                                        placeholder="John"
                                        value={firstName}
                                        onChange={(e) => {
                                            setFirstName(sanitizeInput(e.target.value));
                                            clearFieldError('firstName');
                                        }}
                                    />
                                </div>
                                {fieldErrors.firstName && (
                                    <span className="auth-field-error">{fieldErrors.firstName}</span>
                                )}
                            </div>

                            <div className="auth-form-group">
                                <label htmlFor="lastName">Last Name</label>
                                <div className={`auth-input-wrapper ${fieldErrors.lastName ? 'error' : ''}`}>
                                    <span className="auth-input-icon">👤</span>
                                    <input
                                        type="text"
                                        id="lastName"
                                        placeholder="Doe"
                                        value={lastName}
                                        onChange={(e) => {
                                            setLastName(sanitizeInput(e.target.value));
                                            clearFieldError('lastName');
                                        }}
                                    />
                                </div>
                                {fieldErrors.lastName && (
                                    <span className="auth-field-error">{fieldErrors.lastName}</span>
                                )}
                            </div>
                        </div>

                        {/* Username */}
                        <div className="auth-form-group">
                            <label htmlFor="username">Username</label>
                            <div className={`auh-input-wrapper ${fieldErrors.username ? 'error' : ''}`}>
                                <span className="auth-input-icon">✏️</span>
                                <input
                                    type="text"
                                    id="username"
                                    placeholder="Choose a username"
                                    value={userName}
                                    onChange={(e) => {
                                        setUserName(sanitizeInput(e.target.value));
                                        clearFieldError('username');
                                    }}
                                    autoComplete="username"
                                />
                            </div>
                            {fieldErrors.username && (
                                <span className="auth-field-error">{fieldErrors.username}</span>
                            )}
                        </div>

                        {/* Email */}
                        <div className="auth-form-group">
                            <label htmlFor="email">Email</label>
                            <div className={`auth-input-wrapper ${fieldErrors.email ? 'error' : ''}`}>
                                <span className="auth-input-icon">📧</span>
                                <input
                                    type="text"
                                    id="email"
                                    placeholder="john@example.com"
                                    value={email}
                                    onChange={(e) => {
                                        setEmail(sanitizeInput(e.target.value));
                                        clearFieldError('email');
                                    }}
                                    autoComplete="email"
                                />
                            </div>
                            {fieldErrors.email && (
                                <span className="auth-field-error">{fieldErrors.email}</span>
                            )}
                        </div>

                        {/* Password */}
                        <div className="auth-form-group">
                            <label htmlFor="password">Password</label>
                            <div className={`auth-input-wrapper ${fieldErrors.password ? 'error' : ''}`}>
                                <span className="auth-input-icon">🔒</span>
                                <input
                                    type="password"
                                    id="password"
                                    placeholder="At least 8 characters"
                                    value={password}
                                    onChange={(e) => {
                                        setPassword(e.target.value);
                                        clearFieldError('password');
                                    }}
                                    autoComplete="new-password"
                                />
                            </div>
                            {fieldErrors.password && (
                                <span className="auth-field-error">{fieldErrors.password}</span>
                            )}
                        </div>

                        {/* Confirm Password */}
                        <div className="auth-form-group">
                            <label htmlFor="confirmPassowrd">Confirm Password</label>
                            <div className={`auth-input-wrapper ${fieldErrors.confirmPassword ? 'error' : ''}`}>
                                <span className="auth-input-icon">🔒</span>
                                <input
                                    type="password"
                                    id="confirmPassword"
                                    placeholder="Re-enter your password"
                                    value={confirmPassword}
                                    onChange={(e) => {
                                        setConfirmPassword(e.target.value);
                                        clearFieldError('confirmPassword');
                                    }}
                                    autoComplete="new-password"
                                />
                            </div>
                            {fieldErrors.confirmPassword && (
                                <span className="auth-field-error">{fieldErrors.confirmPassword}</span>
                            )}
                        </div>

                        <button
                            type="submit"
                            className="auth-submit-btn"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <span className="auth-spinner" />
                                    Creating account...
                                </>
                            ) : (
                                'Create Account'
                            )}
                        </button>
                    </form>

                    <div className="auth-footer">
                        <p>
                            Already have an account?{' '}
                            <Link to="/login" className="auth-link">
                                Sign in
                            </Link>
                        </p>
                    </div>
                </div>

                <button className="auth-back-btn" onClick={() => navigate('/')}>
                    ← Back to home
                </button>
            </div>
        </div>
    );
};

export default Register;