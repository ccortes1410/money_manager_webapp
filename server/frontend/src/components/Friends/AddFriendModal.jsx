import React, { useState, useEffect, useCallback } from 'react';

const AddFriendModal = ({ onClose, onSendRequest }) => {
    const [ searchQuery, setSearchQuery ] = useState("");
    const [ searchResults, setSearchResults ] = useState([]);
    const [ loading, setLoading ] = useState(false);
    const [ error, setError ] = useState("");
    const [ successMessage, setSuccessMessage ] = useState("");
    const [ sendingTo, setSendingTo ] = useState(null);

    const baseUrl = "/djangoapp";

    const searchUsers = useCallback(async (query) => {
        if (query.length < 2) {
            setSearchResults([]);
            return;
        }

        setLoading(true);
        setError("");

        try {
            const res = await fetch(
                `${baseUrl}/friends/search?q=${encodeURIComponent(query)}`,
                { credentials: 'include' }
            );
            const data = await res.json();

            if (res.ok) {
                setSearchResults(data.users || []);
            } else {
                setError(data.error || "Search failed");
            }
        } catch (error) {
            console.error("Search error:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const timer = setTimeout(() => {
            searchUsers(searchQuery);
        }, 300);

        return () => clearTimeout(timer);
    }, [searchQuery, searchUsers]);

    const handleSendRequest = async (user) => {
        setSendingTo(user.id);
        setError("");
        setSuccessMessage("");

        const result = await onSendRequest(user.id);

        if (result.success) {
            setSuccessMessage(result.message);
            // Update the local state to reflect the change
            setSearchResults((prev) =>
                prev.map((u) =>
                    u.id === user.id ? { ...u, relationship: "request_sent" } : u
                )
            );
        } else {
            setError(result.message);
        }

        setSendingTo(null);
    };

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

    const getRelationShipButton = (user) => {
        switch (user.relationship) {
            case "friends":
                return (
                    <span className="relationship-badge friends">
                        ✓ Friends
                    </span>
                );
            case "request_sent":
                return (
                    <span className="relationship-badge pending">
                        Request Sent
                    </span>
                );
            case "request_received":
                return (
                    <span className="relationship-badge pending">
                        Sent You a Request
                    </span>
                );
            default:
                return (
                    <button
                        className="send-request-btn"
                        onClick={() => handleSendRequest(user)}
                        disabled={sendingTo === user.id}
                    >
                        {sendingTo === user.id ? "Sending..." : "+ Add Friend"}
                    </button>
                );
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content add-friend-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Add Friend</h2>
                    <button className="modal-close-btn" onClick={onClose}>
                        ×
                    </button>
                </div>

                <div className="modal-body">
                    {/* Search Input */}
                    <div className="search-input-container">
                        <span className="search-icon">🔍</span>
                        <input
                            type="text"
                            placeholder="Search by username or email..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            autoFocus
                        />
                        {searchQuery && (
                            <button
                                className="clear-search"
                                onClick={() => setSearchQuery("")}
                            >
                                ✕
                            </button>
                        )}
                    </div>

                    {/* Messages */}
                    {error && <div className="error-message">{error}</div>}
                    {successMessage && (
                        <div className="success-message">{successMessage}</div>
                    )}

                    {/* Search Results */}
                    <div className="search-results">
                        {loading ? (
                            <div className="loading-state">Searching...</div>
                        ) : searchQuery.length < 2 ? (
                            <div className="hint-state">
                                <span className="hint-icon">💡</span>
                                <p>Enter at least 2 characters to search</p>
                            </div>
                        ) : searchResults.length === 0 ? (
                            <div className="empty-state">
                                <span className="empty-icon">🔍</span>
                                <h3>No users found</h3>
                                <p>Try a different search term</p>
                            </div>
                        ) : (
                            <ul className="user-list">
                                {searchResults.map((user) => (
                                    <li key={user.id} className="user-item">
                                        <div
                                            className="user-avatar"
                                            style={{
                                                backgroundColor: getAvatarColor(user.username),
                                            }}
                                        >
                                            {getInitials(user)}
                                        </div>
                                        <div className="user-info">
                                            <span className="user-name">
                                                {getDisplayName(user)}
                                            </span>
                                            <span className="user-username">
                                                @{user.username}
                                            </span>
                                        </div>
                                        {getRelationShipButton(user)}
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AddFriendModal;