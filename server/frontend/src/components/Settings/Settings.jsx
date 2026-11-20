import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import { useToast } from '../Toast/ToastContext';
import { apiFetch } from '../../utils/csrf';
import './Settings.css';

const Settings = () => {
    const { user, setUser } = useContext(AuthContext);
    const toast = useToast();
    const navigate = useNavigate();

    // Profile state
    const [profile, setProfile] = useState({
        username: user?.username || '',
        first_name: user?.first_name || '',
        last_name: user?.last_name || '',
        email: user?.email || '',
        date_joined: user?.date_joined || '',
    });
    const [profileLoading, setProfileLoading] = useState(true);
    const [profileSaving, setProfileSaving] = useState(false);

    // Password change state
    const [passwordForm, setPasswordForm] = useState({
        current_password: '',
        new_password: '',
        confirm_password: '',
    });
    const [passwordSaving, setPasswordSaving] = useState(false);
    const [passwordError, setPasswordError] = useState('');

    // Delete account state
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [deletePassword, setDeletePassword] = useState('');
    const [deleting, setDeleting] = useState(false);
    const [deleteError, setDeleteError] = useState('');

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const res = await apiFetch('/djangoapp/profile', { method: 'GET' });
                if (res.ok) {
                    const data = await res.json();
                    const p = data.user || data;
                    setProfile({
                        username: p.username || '',
                        first_name: p.first_name || '',
                        last_name: p.last_name || '',
                        email: p.email || '',
                        date_joined: p.date_joined || '',
                    });
                }
            } catch (err) {
                console.error('Error fetching profile:', err);
                toast.error('Failed to load profile');
            } finally {
                setProfileLoading(false);
            }
        };
        fetchProfile();
    }, [toast]);

    const handleProfileSave = async (e) => {
        e.preventDefault();
        setProfileSaving(true);
        try {
            const res = await apiFetch('/djangoapp/profile', {
                method: 'PATCH',
                body: JSON.stringify({
                    first_name: profile.first_name.trim(),
                    last_name: profile.last_name.trim(),
                    email: profile.email.trim(),
                }),
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok) {
                const updated = data.user || {};
                setProfile((prev) => ({
                    ...prev,
                    first_name: updated.first_name ?? prev.first_name,
                    last_name: updated.last_name ?? prev.last_name,
                    email: updated.email ?? prev.email,
                }));
                setUser((prev) => ({
                    ...(prev || {}),
                    ...updated,
                    is_authenticated: true,
                }));
                toast.success('Profile updated');
            } else {
                toast.error(data.error || 'Failed to update profile');
            }
        } catch (err) {
            console.error('Profile update error:', err);
            toast.error('Something went wrong');
        } finally {
            setProfileSaving(false);
        }
    };

    const handlePasswordChange = async (e) => {
        e.preventDefault();
        setPasswordError('');

        if (!passwordForm.current_password) {
            setPasswordError('Please enter your current password.');
            return;
        }
        if (passwordForm.new_password.length < 8) {
            setPasswordError('New password must be at least 8 characters.');
            return;
        }
        if (passwordForm.new_password !== passwordForm.confirm_password) {
            setPasswordError('New passwords do not match.');
            return;
        }

        setPasswordSaving(true);
        try {
            const res = await apiFetch('/djangoapp/profile/change-password', {
                method: 'POST',
                body: JSON.stringify({
                    current_password: passwordForm.current_password,
                    new_password: passwordForm.new_password,
                }),
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok) {
                setPasswordForm({
                    current_password: '',
                    new_password: '',
                    confirm_password: '',
                });
                toast.success('Password updated successfully');
            } else {
                setPasswordError(data.error || 'Failed to update password');
            }
        } catch (err) {
            console.error('Change password error:', err);
            setPasswordError('Something went wrong. Please try again.');
        } finally {
            setPasswordSaving(false);
        }
    };

    const handleDeleteAccount = async (e) => {
        e.preventDefault();
        setDeleteError('');

        if (!deletePassword) {
            setDeleteError('Please enter your password to confirm.');
            return;
        }

        setDeleting(true);
        try {
            const res = await apiFetch('/djangoapp/profile/delete', {
                method: 'DELETE',
                body: JSON.stringify({ password: deletePassword }),
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok) {
                setUser(null);
                toast.info('Your account has been permanently deleted.');
                navigate('/', { replace: true });
            } else {
                setDeleteError(data.error || 'Failed to delete account');
            }
        } catch (err) {
            console.error('Delete account error:', err);
            setDeleteError('Something went wrong. Please try again.');
        } finally {
            setDeleting(false);
        }
    };

    const formattedJoined = profile.date_joined
        ? new Date(profile.date_joined).toLocaleDateString(undefined, {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
          })
        : '';

    return (
        <div className="settings-page">
            <div className="settings-header">
                <h1>Settings</h1>
                <p>Manage your profile, security, and account preferences</p>
            </div>

            {profileLoading ? (
                <div className="settings-loading">Loading your settings...</div>
            ) : (
                <div className="settings-grid">
                    {/* Profile Card */}
                    <section className="settings-card">
                        <div className="settings-card-header">
                            <div className="settings-avatar-lg">
                                {(profile.username || 'U').charAt(0).toUpperCase()}
                            </div>
                            <div>
                                <h2>Profile Information</h2>
                                <p className="settings-meta">
                                    @{profile.username}
                                    {formattedJoined ? ` • Member since ${formattedJoined}` : ''}
                                </p>
                            </div>
                        </div>

                        <form onSubmit={handleProfileSave} className="settings-form">
                            <div className="settings-form-row">
                                <div className="settings-field">
                                    <label htmlFor="settings-first-name">First Name</label>
                                    <input
                                        id="settings-first-name"
                                        type="text"
                                        value={profile.first_name}
                                        onChange={(e) =>
                                            setProfile({ ...profile, first_name: e.target.value })
                                        }
                                        placeholder="First name"
                                    />
                                </div>
                                <div className="settings-field">
                                    <label htmlFor="settings-last-name">Last Name</label>
                                    <input
                                        id="settings-last-name"
                                        type="text"
                                        value={profile.last_name}
                                        onChange={(e) =>
                                            setProfile({ ...profile, last_name: e.target.value })
                                        }
                                        placeholder="Last name"
                                    />
                                </div>
                            </div>

                            <div className="settings-field">
                                <label htmlFor="settings-email">Email Address</label>
                                <input
                                    id="settings-email"
                                    type="email"
                                    value={profile.email}
                                    onChange={(e) =>
                                        setProfile({ ...profile, email: e.target.value })
                                    }
                                    placeholder="you@example.com"
                                />
                                <span className="settings-hint">
                                    Used for password reset links and account notifications.
                                </span>
                            </div>

                            <div className="settings-actions">
                                <button
                                    type="submit"
                                    className="settings-btn-primary"
                                    disabled={profileSaving}
                                >
                                    {profileSaving ? 'Saving...' : 'Save Changes'}
                                </button>
                            </div>
                        </form>
                    </section>

                    {/* Change Password Card */}
                    <section className="settings-card">
                        <div className="settings-card-header">
                            <div className="settings-section-icon">🔒</div>
                            <div>
                                <h2>Security &amp; Password</h2>
                                <p className="settings-meta">
                                    Update your password without signing out
                                </p>
                            </div>
                        </div>

                        {passwordError && (
                            <div className="settings-alert error">⚠️ {passwordError}</div>
                        )}

                        <form onSubmit={handlePasswordChange} className="settings-form">
                            <div className="settings-field">
                                <label htmlFor="current-password">Current Password</label>
                                <input
                                    id="current-password"
                                    type="password"
                                    value={passwordForm.current_password}
                                    onChange={(e) =>
                                        setPasswordForm({
                                            ...passwordForm,
                                            current_password: e.target.value,
                                        })
                                    }
                                    placeholder="Enter current password"
                                    autoComplete="current-password"
                                />
                            </div>

                            <div className="settings-form-row">
                                <div className="settings-field">
                                    <label htmlFor="new-password">New Password</label>
                                    <input
                                        id="new-password"
                                        type="password"
                                        value={passwordForm.new_password}
                                        onChange={(e) =>
                                            setPasswordForm({
                                                ...passwordForm,
                                                new_password: e.target.value,
                                            })
                                        }
                                        placeholder="At least 8 characters"
                                        autoComplete="new-password"
                                    />
                                </div>
                                <div className="settings-field">
                                    <label htmlFor="confirm-new-password">Confirm New Password</label>
                                    <input
                                        id="confirm-new-password"
                                        type="password"
                                        value={passwordForm.confirm_password}
                                        onChange={(e) =>
                                            setPasswordForm({
                                                ...passwordForm,
                                                confirm_password: e.target.value,
                                            })
                                        }
                                        placeholder="Re-enter new password"
                                        autoComplete="new-password"
                                    />
                                </div>
                            </div>

                            <div className="settings-actions">
                                <button
                                    type="submit"
                                    className="settings-btn-primary"
                                    disabled={passwordSaving}
                                >
                                    {passwordSaving ? 'Updating...' : 'Update Password'}
                                </button>
                            </div>
                        </form>
                    </section>

                    {/* Danger Zone */}
                    <section className="settings-card danger-card">
                        <div className="settings-card-header">
                            <div className="settings-section-icon danger">⚠️</div>
                            <div>
                                <h2>Danger Zone</h2>
                                <p className="settings-meta">
                                    Permanently delete your account and all associated financial data
                                </p>
                            </div>
                        </div>

                        {!showDeleteConfirm ? (
                            <div className="settings-actions">
                                <button
                                    type="button"
                                    className="settings-btn-danger-outline"
                                    onClick={() => setShowDeleteConfirm(true)}
                                >
                                    Delete Account
                                </button>
                            </div>
                        ) : (
                            <form onSubmit={handleDeleteAccount} className="settings-form">
                                {deleteError && (
                                    <div className="settings-alert error">⚠️ {deleteError}</div>
                                )}
                                <p className="danger-warning-text">
                                    This action cannot be undone. Enter your password to permanently
                                    delete <strong>@{profile.username}</strong>.
                                </p>
                                <div className="settings-field">
                                    <label htmlFor="delete-confirm-password">Confirm Password</label>
                                    <input
                                        id="delete-confirm-password"
                                        type="password"
                                        value={deletePassword}
                                        onChange={(e) => setDeletePassword(e.target.value)}
                                        placeholder="Enter your password"
                                        autoComplete="current-password"
                                    />
                                </div>
                                <div className="settings-actions">
                                    <button
                                        type="button"
                                        className="settings-btn-secondary"
                                        onClick={() => {
                                            setShowDeleteConfirm(false);
                                            setDeletePassword('');
                                            setDeleteError('');
                                        }}
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="settings-btn-danger"
                                        disabled={deleting}
                                    >
                                        {deleting ? 'Deleting...' : 'Permanently Delete'}
                                    </button>
                                </div>
                            </form>
                        )}
                    </section>
                </div>
            )}
        </div>
    );
};

export default Settings;
