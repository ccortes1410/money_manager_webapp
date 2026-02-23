import React, { useContext, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import { useToast } from '../Toast/ToastContext';
import { apiFetch } from '../../utils/csrf';
import { sanitizeInput } from '../../utils/sanitize';
import './Login.css';

const Login = () => {
    const [ userName, setUserName ] = useState('');
    const [ password, setPassword ] = useState('');
    const [ error, setError ] = useState('');
    const [ loading, setLoading ] = useState(false);

    const { setUser } = useContext(AuthContext);
    const navigate = useNavigate();
    const login_url = "/djangoapp/login";
    const toast = useToast();

    // const from = location.state?.from?.pathname || "/dashboard";

    const login = async (e) => {
        e.preventDefault();
        setError('');

        if (!userName.trim() || !password.trim()) {
            setError('Please enter both username and password.')
            return;
        }

        setLoading(true);

        try {
            const res = await apiFetch(login_url, {
                method: 'POST',
                body: JSON.stringify({
                    username: sanitizeInput(userName),
                    password: password
                }),
            });

            if (res.ok) {
                const user = await res.json();
                setUser(user);
                toast.success(`Welcome back, ${user.username}!`);
                navigate('/dashboard');
            } else {
                setError('Invalid username or password. Please try again.');
            }
        } catch (error) {
            console.error("Login error:", error);
            setError("Something went wrong. Please try again later.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-bg">
                <div className="auth-glow glow-1" />
                <div className="auth-glow glow-2" />
            </div>

            <div className="auth-container">
                {/* Branding */}
                <Link to="/" className="auth-logo">
                    <span className="auth-logo-icon">💰</span>
                    <span className="auth-logo-text">Money Manager</span>
                </Link>

                {/* Card */}
                <div className="auth-card">
                    <div className="auth-card-header">
                        <h1>Welcome back</h1>
                        <p>Sign in to your account to continue</p>
                    </div>

                    {error && (
                        <div className="auth-error">
                            <span className="auth-error-icon">⚠️</span>
                            {error}
                        </div>
                    )}

                    <form onSubmit={login} className="auth-form">
                        <div className="auth-form-group">
                            <label htmlFor="username">Username</label>
                            <div className="auth-input-wrapper">
                                <span className="auth-input-icon">👤</span>
                                <input
                                    type="text"
                                    id="username"
                                    placeholder="Enter your username"
                                    value={userName}
                                    onChange={(e) => 
                                        setUserName(sanitizeInput(e.target.value))}
                                    autoComplete="username"
                                    autoFocus
                                />
                            </div>
                        </div>

                        <div className="auth-form-group">
                            <label htmlFor="password">Password</label>
                            <div className="auth-input-wrapper">
                                <span className="auth-input-icon">🔒</span>
                                <input
                                    type="password"
                                    id="password"
                                    placeholder="Enter your password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    autoComplete="current-password"
                                />                            
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="auth-submit-btn"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <span className="auth-spinner" />
                                    Signing in...
                                </>
                            ) : (
                                'Sign In'
                            )}
                        </button>
                    </form>

                    <div className="auth-footer">
                        <p>
                            Don't have an account?{' '}
                            <Link to="/register" className="auth-link">
                                Create one free
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

export default Login;