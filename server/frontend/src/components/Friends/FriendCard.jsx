import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAvatarColor, getInitials, getDisplayName } from '../../utils/formatters';

const FriendCard = ({ friend, onRemove }) => {
    const [ showMenu, setShowMenu ] = useState(false);
    const navigate = useNavigate();

    const formatDate = (dateString) => {
        if (!dateString) return "Recently";
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            month: "short",
            year: "numeric",
        });
    };

    return (
        <div className="friend-card">
            <div className="friend-card-header">
                <div 
                    className="friend-avatar"
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
                                    navigate("/shared-budgets");
                                }}
                            >
                                🤝 Shared Budgets
                            </button>
                            <button
                                className="menu-item danger"
                                onClick={() => {
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