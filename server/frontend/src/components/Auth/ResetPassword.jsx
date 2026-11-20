import React, { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { apiFetch } from '../../utils/csrf';
import { useToast } from '../Toast/ToastContext';
import './Login.css';

const ResetPassword = () => {
    const { uid, token } = useParams();
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const toast = useToast();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!newPassword || newPassword.length < 8) {
            setError('Password must be at least 8 characters long.');
            return;
        }
        if (newPassword !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        setLoading(true);
        try {
            const res = await apiFetch('/djangoapp/password-reset/confirm', {
                method: 'POST',
                body: JSON.stringify({
                    uid,
                    token,
                    new_password: newPassword,
                }),
            });

            const data = await res.json().catch(() => ({}));
            if (res.ok) {
                toast.success('Password reset successfully! Please sign in.');
                navigate('/login', { replace: true });
            } else {
                setError(data.error || 'Reset link is invalid or has expired.');
            }
        } catch (err) {
            console.error('Password reset confirm error:', err);
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
                        <h1>Set a new password</h1>
                        <p>Choose a strong password for your account</p>
                    </div>

                    {error && (
                        <div className="auth-error">
                            <span className="auth-error-icon">⚠️</span>
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="auth-form">
                        <div className="auth-form-group">
                            <label htmlFor="new-password">New Password</label>
                            <div className="auth-input-wrapper">
                                <span className="auth-input-icon">🔒</span>
                                <input
                                    type="password"
                                    id="new-password"
                                    placeholder="At least 8 characters"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    autoComplete="new-password"
                                    autoFocus
                                />
                            </div>
                        </div>

                        <div className="auth-form-group">
                            <label htmlFor="confirm-password">Confirm New Password</label>
                            <div className="auth-input-wrapper">
                                <span className="auth-input-icon">🔒</span>
                                <input
                                    type="password"
                                    id="confirm-password"
                                    placeholder="Re-enter your new password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    autoComplete="new-password"
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
                                    Updating password...
                                </>
                            ) : (
                                'Reset Password'
                            )}
                        </button>
                    </form>

                    <div className="auth-footer">
                        <p>
                            Need a new link?{' '}
                            <Link to="/forgot-password" className="auth-link">
                                Request another reset
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ResetPassword;
