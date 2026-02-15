import React from 'react';

const FriendRequestCard = ({ request, type, onAccept, onDecline, onCancel }) => {
    const user = type === "received" ? request?.from_user : request?.to_user;

    const getInitials = (user) => {
        if (user.first_name && user.last_name) {
            return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
        }
        return user.username.slice(0, 2).toUpperCase();
    };

    const getDisplayName = (user) => {
        if (user.first_name && user.last_name) {
            return `${user.first_name} ${user.last_name}`;
        }
        return user.username;
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString("en-Us", {
            month: "short",
            day: "numeric",
        });
    };

    const getAvatarColor = (username) => {
        const colors = [
            "#3b82f6",
            "#22c55e",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
            "#ec4899",
            "#06b6d4",
            "#f97316",
        ];
        const index = username.charAt(0) % colors.length;
        return colors[index];
    };

    return (
        <div className="request-card">
            <div
                className="request-avatar"
                style={{ backgroundColor: getAvatarColor(user.username) }}
            >
                {getInitials(user)}
            </div>

            <div className="request-info">
                <h3 className="request-name">{getDisplayName(user)}</h3>
                <p className="request-username">@{user.username}</p>
                <p className="request-time">
                    {type === "received" ? "Sent you a request" : "Request sent"}{" "}
                    {formatDate(request.created_at)}
                </p>
            </div>

            <div className="request-actions">
                {type === "received" ? (
                    <>
                        <button className="accept-btn" onClick={onAccept}>
                            ✓ Accept
                        </button>
                        <button className="decline-btn" onClick={onDecline}>
                            ✕ Decline
                        </button>
                    </>
                ) : (
                    <button className="cancel-btn" onClick={onCancel}>
                        Cancel Request
                    </button>
                )}
            </div>
        </div>
    );
};

export default FriendRequestCard;