import React, { useState } from 'react';

const FriendCard = ({ friend, onRemove }) => {
    const [ showMenu, setShowMenu ] = useState(false);

    const getInitials = (friend) => {
        if (friend.first_name && friend.last_name) {
            return `${friend.first_name[0]}${friend.last_name[0]}`.toUpperCase();
        }
        return friend.username.slice(0, 2).toUpperCase();
    };

    const getDisplayName = (friend) => {
        if (friend.first_name && friend.last_name) {
            return `${friend.first_name} ${friend.last_name}`;
        }
        return friend.username;
    };

    const formatDate = (dateString) => {
        if (!dateString) return "Recently";
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            month: "short",
            year: "numeric",
        });
    };

    const getAvatarColor = (username) => {
        const colors = [
            "#3b82f6", // blue
            "#22c55e", // green
            "#f59e0b", // amber
            "#ef4444", // red
            "#8b5cf6", // violet
            "#ec4899", // pink
            "#06b6d4", // cyan
            "#f97316", // orange
        ];
        const index = username.charAt(0) % colors.length;
        return colors[index];
    };

    return (
        <div className="friend-card">
            <div className="friend-card-header">
                <div 
                    className="frien-avatar"
                    style={{ backgroundColor: getAvatarColor(friend.username) }}
                >
                    {getInitials(friend)}
                </div>
                <div className="friend-menu-container">
                    <button
                        className="friend-menu-btn"
                        onClick={() => setShowMenu(!showMenu)}
                    >
                        ⋮
                    </button>
                    {showMenu && (
                        <div className="friend-menu">
                            <button
                                className="menu-item"
                                onClick={() => {
                                    setShowMenu(false);
                                    // TODO: Navigate to shared budgets with this friend
                                }}
                            >
                                🤝 Shared Budgets
                            </button>
                            <button
                                className="menu-item danger"
                                onRemove={() => {
                                    setShowMenu(false);
                                    onRemove();
                                }}
                            >
                                ❌ Remove Friend
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <div className="friend-card-body">
                <h3 className="friend-name">{getDisplayName(friend)}</h3>
                <p className='friend-username'>@{friend.username}</p>
                {friend.email && <p className="friend-email">{friend.email}</p>}
            </div>

            <div className="friend-card-footer">
                <span className="friends-since">
                    Friends since {formatDate(friend.friends_since)}
                </span>
                <div className="friend-stats">
                    <span className="friend-stat" title="Shared Budgets">
                        🤝 0
                    </span>
                </div>
            </div>
        </div>
    );
};

export default FriendCard;