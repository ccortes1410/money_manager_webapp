import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../../utils/csrf';
import './NotificationBell.css';

const formatRelativeTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return '';
    const diffMs = Date.now() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return 'Just now';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString();
};

const getNotificationIcon = (item) => {
    if (item.source === 'alert') {
        if (item.type === 'budget_over') return '🚨';
        if (item.type === 'budget_warning') return '⚠️';
        if (item.type === 'subscription_upcoming') return '📅';
        return '🔔';
    }
    if (item.source === 'friend') return '👥';
    if (item.source === 'shared_budget') return '🤝';
    return '🔔';
};

const NotificationBell = ({ collapsed, onNavigate }) => {
    const [open, setOpen] = useState(false);
    const [filter, setFilter] = useState('all'); // 'all' | 'alerts' | 'social'
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [alertsCount, setAlertsCount] = useState(0);
    const [loading, setLoading] = useState(false);
    const containerRef = useRef(null);
    const navigate = useNavigate();

    const fetchNotifications = useCallback(async (showSpinner = false) => {
        if (showSpinner) setLoading(true);
        try {
            const res = await apiFetch('/djangoapp/notifications/all');
            if (!res.ok) return;
            const data = await res.json();
            setNotifications(data.notifications || []);
            setUnreadCount(data.unread_count || 0);
            setAlertsCount(data.alerts_count || 0);
        } catch (err) {
            // Silently ignore polling errors
        } finally {
            if (showSpinner) setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchNotifications(false);
        const interval = setInterval(() => fetchNotifications(false), 60000);
        return () => clearInterval(interval);
    }, [fetchNotifications]);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (containerRef.current && !containerRef.current.contains(e.target)) {
                setOpen(false);
            }
        };
        if (open) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [open]);

    const handleToggle = (e) => {
        e.stopPropagation();
        const nextOpen = !open;
        setOpen(nextOpen);
        if (nextOpen) {
            fetchNotifications(true);
        }
    };

    const handleMarkAllRead = async (e) => {
        e.stopPropagation();
        try {
            const res = await apiFetch('/djangoapp/notifications/all/read-all', { method: 'POST' });
            if (res.ok) {
                setNotifications((prev) =>
                    prev.map((n) => (n.source === 'alert' ? n : { ...n, is_read: true }))
                );
                setUnreadCount(0);
            }
        } catch (err) {
            console.error('Failed to mark all notifications as read', err);
        }
    };

    const handleItemClick = async (item) => {
        if (item.source !== 'alert' && !item.is_read) {
            try {
                if (item.source === 'friend') {
                    await apiFetch(`/djangoapp/notifications/${item.raw_id}/read`, { method: 'POST' });
                } else if (item.source === 'shared_budget') {
                    await apiFetch(`/djangoapp/budget-notifications/${item.raw_id}/read`, { method: 'POST' });
                }
                setNotifications((prev) =>
                    prev.map((n) => (n.id === item.id ? { ...n, is_read: true } : n))
                );
                setUnreadCount((c) => Math.max(0, c - 1));
            } catch (err) {
                console.error('Failed to mark notification read', err);
            }
        }
        setOpen(false);
        if (onNavigate) onNavigate();
        if (item.link) {
            navigate(item.link);
        }
    };

    const filteredItems = notifications.filter((item) => {
        if (filter === 'alerts') return item.source === 'alert';
        if (filter === 'social') return item.source === 'friend' || item.source === 'shared_budget';
        return true;
    });

    const totalBadge = unreadCount + alertsCount;

    return (
        <div className={`notification-bell-wrapper ${collapsed ? 'collapsed' : ''}`} ref={containerRef}>
            <button
                type="button"
                className={`notification-bell-btn ${open ? 'active' : ''}`}
                onClick={handleToggle}
                aria-label="Notifications"
                title="Notifications"
            >
                <span className="notification-bell-icon" aria-hidden="true">🔔</span>
                {totalBadge > 0 && (
                    <span className={`notification-bell-badge ${alertsCount > 0 ? 'has-alert' : ''}`}>
                        {totalBadge > 9 ? '9+' : totalBadge}
                    </span>
                )}
            </button>

            {open && (
                <div className="notification-dropdown" onClick={(e) => e.stopPropagation()}>
                    <div className="notification-dropdown-header">
                        <div className="notification-dropdown-title-row">
                            <span className="notification-dropdown-title">Notifications</span>
                            {unreadCount > 0 && (
                                <button
                                    type="button"
                                    className="notification-mark-all-btn"
                                    onClick={handleMarkAllRead}
                                >
                                    Mark all read
                                </button>
                            )}
                        </div>
                        <div className="notification-filter-tabs">
                            <button
                                type="button"
                                className={`notification-tab ${filter === 'all' ? 'active' : ''}`}
                                onClick={() => setFilter('all')}
                            >
                                All ({notifications.length})
                            </button>
                            <button
                                type="button"
                                className={`notification-tab ${filter === 'alerts' ? 'active' : ''}`}
                                onClick={() => setFilter('alerts')}
                            >
                                Alerts ({alertsCount})
                            </button>
                            <button
                                type="button"
                                className={`notification-tab ${filter === 'social' ? 'active' : ''}`}
                                onClick={() => setFilter('social')}
                            >
                                Social ({notifications.length - alertsCount})
                            </button>
                        </div>
                    </div>

                    <div className="notification-dropdown-list">
                        {loading && notifications.length === 0 ? (
                            <div className="notification-empty">Loading notifications...</div>
                        ) : filteredItems.length === 0 ? (
                            <div className="notification-empty">
                                <span className="notification-empty-icon">✨</span>
                                <p>You're all caught up!</p>
                            </div>
                        ) : (
                            filteredItems.map((item) => {
                                const isUnread = item.source === 'alert' || !item.is_read;
                                return (
                                    <button
                                        type="button"
                                        key={item.id}
                                        className={`notification-item ${isUnread ? 'unread' : ''} ${
                                            item.severity ? `severity-${item.severity}` : ''
                                        }`}
                                        onClick={() => handleItemClick(item)}
                                    >
                                        <span className="notification-item-icon">
                                            {getNotificationIcon(item)}
                                        </span>
                                        <div className="notification-item-body">
                                            {item.title && (
                                                <div className="notification-item-title">{item.title}</div>
                                            )}
                                            <div className="notification-item-message">{item.message}</div>
                                            <div className="notification-item-meta">
                                                {item.source === 'alert' ? (
                                                    <span className="notification-tag alert-tag">Live Alert</span>
                                                ) : (
                                                    <span>{formatRelativeTime(item.created_at)}</span>
                                                )}
                                                {item.budget?.name && (
                                                    <span className="notification-tag">{item.budget.name}</span>
                                                )}
                                            </div>
                                        </div>
                                        {isUnread && <span className="notification-unread-dot" />}
                                    </button>
                                );
                            })
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default NotificationBell;
