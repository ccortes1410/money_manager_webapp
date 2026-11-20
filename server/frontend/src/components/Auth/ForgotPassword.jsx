import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiFetch } from '../../utils/csrf';
import './Login.css';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const [submitted, setSubmitted] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        const trimmed = email.trim();
        if (!trimmed) {
            setError('Please enter your email address.');
            return;
        }

        setLoading(true);
        try {
            const res = await apiFetch('/djangoapp/password-reset/request', {
                method: 'POST',
                body: JSON.stringify({ email: trimmed }),
            });

            if (res.ok) {
                setSubmitted(true);
            } else {
                const data = await res.json().catch(() => ({}));
                setError(data.error || 'Could not process request. Please try again.');
            }
        } catch (err) {
            console.error('Password reset request error:', err);
            setError('Something went wrong. Please try again later.');
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
                <Link to="/" className="auth-logo">
                    <span className="auth-logo-icon">💰</span>
                    <span className="auth-logo-text">Money Manager</span>
                </Link>

                <div className="auth-card">
                    <div className="auth-card-header">
                        <h1>Reset your password</h1>
                        <p>
                            {submitted
                                ? 'Check your inbox for a reset link'
                                : "Enter the email associated with your account and we'll send you a reset link"}
                        </p>
                    </div>

                    {error && (
                        <div className="auth-error">
                            <span className="auth-error-icon">⚠️</span>
                            {error}
                        </div>
                    )}

                    {submitted ? (
                        <div className="auth-success-box">
                            <span className="auth-success-icon">✉️</span>
                            <p>
                                If an account exists for <strong>{email.trim()}</strong>, a password
                                reset link has been sent. The link expires in 1 hour.
                            </p>
                            <Link to="/login" className="auth-submit-btn auth-btn-link">
                                Back to Sign In
                            </Link>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="auth-form">
                            <div className="auth-form-group">
                                <label htmlFor="reset-email">Email address</label>
                                <div className="auth-input-wrapper">
                                    <span className="auth-input-icon">📧</span>
                                    <input
                                        type="email"
                                        id="reset-email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        autoComplete="email"
                                        autoFocus
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
                                        Sending link...
                                    </>
                                ) : (
                                    'Send Reset Link'
                                )}
                            </button>
                        </form>
                    )}

                    <div className="auth-footer">
                        <p>
                            Remember your password?{' '}
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

export default ForgotPassword;
