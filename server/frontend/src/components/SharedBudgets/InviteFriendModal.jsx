import React, { useState, useEffect } from 'react';

const InviteFriendModal = ({ budgetId, existingMembers, onClose, onInvited }) => {
    const [ friends, setFriends ] = useState([]);
    const [ loading, setLoading ] = useState(true);
    const [ sending, setSending ] = useState(null);
    const [ error, setError ] = useState("");
    const [ success, setSuccess ] = useState("");
    const [ searchQuery, setSearchQuery ] = useState("");

    const baseUrl = "/djangoapp";
    const safeExistingMembers = Array.isArray(existingMembers) ? existingMembers : [];

    useEffect(() => {
        fetchFriends();
    }, []);

    const fetchFriends = async () => {
        try {
            const res = await fetch(`${baseUrl}/friends`, {
                credentials: 'include',
            });
            const data = await res.json();

            if (res.ok && data.friends) {
                // Filter out existing members
                const available = (Array.isArray(data.friends) ? data.friends : []).filter(
                    (f) => !safeExistingMembers.includes(f.id)
                );
                setFriends(available);
            }
        } catch (error) {
            console.error("Error fetching friends:", error);
            setError("Failed to load friends");
        } finally {
            setLoading(false);
        }
    };

    const handleInvite = async (friendId, friendName) => {
        setSending(friendId);
        setError("");
        setSuccess("");

        try {
            const res = await fetch(`${baseUrl}/shared-budgets/${budgetId}/invite`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: friendId,
                    role: 'editor',
                }),
            });
            const data = await res.json();

            if (res.ok) {
                setSuccess(`Invitation sent to ${friendName}!`);
                // Remove invited friend from list
                setFriends((prev) => prev.filter((f) => f.id !== friendId));
                if (onInvited) onInvited();
            } else {
                setError(data.error || "Failed to send invitation");
            }
        } catch (error) {
            console.error("Error inviting friend:", error);
            setError("An error ocurred");
        } finally {
            setSending(null);
        }
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
            "#f97316"
        ];
        if (!username) return colors[0];
        return colors[username.charAt(0) & colors.length];
    };

    const getInitials = (friend) => {
        if (friend.first_name && friend.last_name) {
            return `${friend.first_name[0]}${friend.last_name[0]}`.toUpperCase();
        }
        return friend.username?.slice(0, 2).toUpperCase() || "??";
    };

    const getDisplayName = (friend) => {
        if (friend.first_name && friend.last_name) {
            return `${friend.first_name} ${friend.last_name}`;
        }
        return friend.username || "Unknown";
    };

    const filteredFriends = friends.filter((friend) => {
        if (!searchQuery) return true;
        const query = searchQuery.toLocaleLowerCase();
        return (
            friend.username?.toLowerCase().includes(query) ||
            friend.first_name?.toLowerCase().includes(query) ||
            friend.last_name?.toLowerCase().includes(query) ||
            friend.email?.toLowerCase().includes(query) 
        );
    });

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content sb-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>👥 Invite Friends</h2>
                    <button className="modal-close-btn" onClick={onClose}>×</button>
                </div>

                <div className="sb-modal-form">
                    {/* Search */}
                    <div className="sb-invite-search">
                        <span className="sb-search-icon">🔍</span>
                        <input
                            type="text"
                            placeholder="Search friends..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            autoFocus
                        />
                        {searchQuery && (
                            <button
                                className="sb-clear-search"
                                onClick={() => setSearchQuery("")}
                            >
                                ✕
                            </button>
                        )}
                    </div>

                    {/* Messages */}
                    {error && <div className="sb-error-message">{error}</div>}
                    {success && <div className="sb-success-message">{success}</div>}

                    {/* Friends List */}
                    <div className="sb-invite-list">
                        {loading ? (
                            <div className="sb-loading-text">Loading friends...</div>
                        ) : filteredFriends.length === 0 ? (
                            <div className="sb-invite-empty">
                                {friends.length === 0 ? (
                                    <>
                                        <span className="sb-empty-icon">👥</span>
                                        <h3>No friends to invite</h3>
                                        <p>All your friends are already members, or you haven't added friends yet.</p>
                                    </>
                                ): (
                                    <>
                                        <span className="sb-empty-icon">🔍</span>
                                        <h3>No matches found</h3>
                                        <p>Try a different search term</p>
                                    </>
                                )}
                            </div>
                        ) : (
                            filteredFriends.map((friend) => (
                                <div key={friend.id} className="sb-invite-item">
                                    <div
                                        className="sb-invite-avatar"
                                        style={{
                                            backgroundColor: getAvatarColor(friend.username),
                                        }}
                                    >
                                        {getInitials(friend)}
                                    </div>
                                    <div className="sb-invite-info">
                                        <span className="sb-invite-name">
                                            {getDisplayName(friend)}
                                        </span>
                                        <span className="sb-invite-username">
                                            @{friend.username}
                                        </span>
                                    </div>
                                    <button
                                        className="sb-invite-btn"
                                        onClick={() => handleInvite(friend.id, getDisplayName(friend))}
                                        disabled={sending === friend.id}
                                    >
                                        {sending === friend.id ? "Sending..." : "Invite"}
                                    </button>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Close Button */}
                    <div className="sb-modal-actions">
                        <button className="sb-cancel-btn" onClick={onClose}>
                            Done
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InviteFriendModal;