import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../AuthContext';
import FriendCard from  './FriendCard';
import FriendRequestCard from './FriendRequestCard';
import AddFriendModal from './AddFriendModal';
import './Friends.css';

const Friends = () => {
    const [ friends, setFriends ] = useState([]);
    const [ receivedRequests, setReceivedRequests ] = useState([]);
    const [ sentRequests, setSentRequests ] = useState([]);
    const [ loading, setLoading ] = useState(true);
    const [ showAddModal, setShowAddModal ] = useState(false);
    const [ activeTab, setActiveTab ] = useState("friends");
    const [ searchQuery, setSearchQuery ] = useState("");

    const { user } = useContext(AuthContext);
    const navigate = useNavigate();

    const baseUrl = "/djangoapp";

    const fetchFriendData = async () => {
        setLoading(true);
        try { 
            const friendsRes = await fetch(baseUrl+`/friends`, {
                credentials: 'include',
            });
            const friendsData = await friendsRes.json();

            if (friendsData.friends) {
                setFriends(friendsData.friends);
            }
            
            // Fetch pending requests
            const requestsRes = await fetch(baseUrl+`/friends/requests`, {
                credentials: 'include',
            });
            const requestsData = await requestsRes.json();

            if (requestsData.received_requests) {
                setReceivedRequests(requestsData.received_requests);
            }
            if (requestsData.sent_requests) {
                setSentRequests(requestsData.sent_requests);
            }
        } catch (error) {
            console.error('Error fetching friend data:', error);
        } finally {
            setLoading(false);
        }
    };
    console.log("Sent Requests:", sentRequests)
    console.log("Received Requests:", receivedRequests)
    const handleAcceptRequest = async (friendshipId) => {
        try {
            const res = await fetch(baseUrl+`/friends/request/${friendshipId}/respond`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'accept' }),
            })

            const data = await res.json();

            if (res.ok) {
                fetchFriendData();
            } else {
                alert(data.error || 'Failed to accept request');
            }
        } catch (error) {
            console.error("Error accepting request:", error);
        }
    };

    const handleDeclineRequest = async (friendshipId) => {
        try {
            const res = await fetch(baseUrl+`/friends/request/${friendshipId}/respond`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'decline' }),
            });

            const data = await res.json();

            if (res.ok) {
                fetchFriendData();
            } else {
                alert(data.error || "Failed to decline request");
            }
        } catch (error) {
            console.error("Error declining request:", error);
        }
    };

    const handleCancelRequest = async (friendshipId) => {
        if (!window.confirm("Cancel this friend request?")) return;

        try {
            const res = await fetch(baseUrl+`/friends/request/${friendshipId}/cancel`, {
                method: 'DELETE',
                credentials: 'include',
            });

            const data = await res.json();

            if (res.ok) {
                fetchFriendData();
            } else {
                alert(data.error || "Failed to cancel request");
            }
        } catch (error) {
            console.error("Error cancelling request:", error);
        }
    };

    const handleRemoveFriend = async (friendId, friendUsername) => {
        if (!window.confirm(`Remove ${friendUsername} from your friends?`)) return;

        try {
            const res = await fetch(baseUrl+`/friends/${friendId}/remove`, {
                method: 'DELETE',
                credentials: 'include',
            });

            const data = await res.json();

            if (res.ok) {
                fetchFriendData();
            } else {
                alert(data.error || "Failed to remove friend");
            }
        } catch (error) {
            console.error("Error removing friend:", error);
        }
    };

    const handleSendRequest = async (userId) => {
        try {
            const res = await fetch(baseUrl+`/friends/request`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId }),
            });

            const data = await res.json();

            if (res.ok) {
                fetchFriendData();
                return { success: true, message: data.message };
            } else {
                return { success: false, message: data.message };
            }
        } catch (error) {
            console.error("Error sending request:", error);
            return { success: false, message: "An error occurred" };
        }
    };

    const filteredFriends = friends.filter((friend) => {
        if (!searchQuery) return true;
        const query = searchQuery.toLowerCase();
        return (
            friend.username.toLowerCase().includes(query) ||
            friend.email?.toLowerCase().includes(query) ||
            friend.first_name?.toLowerCase().includes(query) ||
            friend.last_name?.toLowerCase().includes(query) 
        );
    });

    useEffect(() => {
        fetchFriendData();
    }, []);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate("/login");
        }
    }, [user, navigate]);

    const totalPendingCount = receivedRequests.length;

    return (
        <div className="friends-page">
            {/* Header */}
            <div className="friends-header">
                <div className="friends-header-left">
                    <h1>Friends</h1>
                    {totalPendingCount > 0 && (
                        <span className="pending-badge">{totalPendingCount} pending</span>
                    )}
                </div>
                <button
                    className="add-friend-btn"
                    onClick={() => setShowAddModal(true)}
                >
                    + Add Friend
                </button>
            </div>

            {/* Stats Cards */}
            <div className="friends-stats">
                <div className="stat-card">
                    <span className="stat-icon">👥</span>
                    <div className="stat-info">
                        <span className="stat-value">{friends.length}</span>
                        <span className="stat-label">Friends</span>
                    </div>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">📥</span>
                    <div className="stat-info">
                        <span className="stat-value">{receivedRequests.length}</span>
                        <span className="stat-label">Received Requests</span>
                    </div>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">📥</span>
                    <div className="stat-info">
                        <span className="stat-value">0</span>
                        <span className="stat-label">Shared Budgets</span>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="friends-tabs">
                <button
                    className={`tab-btn ${activeTab === "friends" ? "active" : ""}`}
                    onClick={() => setActiveTab("friends")}
                >
                    Friends
                    <span className="tab-count">{friends.length}</span>
                </button>
                <button
                    className={`tab-btn ${activeTab === "received" ? "active" : ""}`}
                    onClick={() => setActiveTab("received")}
                >
                    Received
                    {receivedRequests.length > 0 && (
                        <span className="tab-count alert">{receivedRequests.length}</span>
                    )}
                </button>
                <button
                    className={`tab-btn ${activeTab === "sent" ? "active" : ""}`}
                    onClick={() => setActiveTab("sent")}
                >
                    Sent
                    {sentRequests.length > 0 && (
                        <span className="tab-count">{sentRequests.length}</span>
                    )}
                </button>
            </div>

            {/* Content */}
            <div className="friends-content">
                {/* Friends Tab */}
                {activeTab === "friends" && (
                    <>
                        {/* Search Bar */}
                        <div className="friends-search">
                            <span classname="search-icon">🔍</span>
                            <input
                                id="search"
                                type="text"
                                placeholder="Search friends..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
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

                        {/* Friends Grid */}
                        {loading ? (
                            <div className="loading-state">Loading friends...</div>
                        ) : filteredFriends.length === 0 ? (
                            <div className="empty-state">
                                {searchQuery ? (
                                    <>
                                        <span className="empty-icon">🔍</span>
                                        <h3>No friends found</h3>
                                        <p>No friends match "{searchQuery}"</p>
                                    </>
                                ) : (
                                    <>
                                        <span className="empty-icon">👥</span>
                                        <h3>No friends yet</h3>
                                        <p>Add friends to share budgets and track expenses together!</p>
                                        <button
                                            className="add-friend-btn"
                                            onClick={() => setShowAddModal(true)}
                                        >
                                            + Add Your First Friend
                                        </button>
                                    </>
                                )}
                            </div>
                        ): (
                            <div className="friends-grid">
                                {filteredFriends.map((friend) => (
                                    <FriendCard
                                        key={friend.id}
                                        friend={friend}
                                        onRemove={() => handleRemoveFriend(friend.id, friend.username)}
                                    />
                                ))}
                            </div>
                        )}
                    </>
                )}

                {/* Received Requests Tab */}
                {activeTab === "received" && (
                    <>
                        {loading ? (
                            <div className="loading-state">Loading requests...</div>
                        ) : receivedRequests.length === 0 ? (
                            <div className="empty-state">
                                <span className="empty-icon">📥</span>
                                <h3>No pending requests</h3>
                                <p>You don't have any pending friend requests.</p>
                            </div>
                        ) : (
                            <div className="requests-list">
                                {receivedRequests.map((request) => (
                                    <FriendRequestCard
                                        key={request.id}
                                        request={request}
                                        type="received"
                                        onAccept={() => handleAcceptRequest(request.id)}
                                        onDecline={() => handleDeclineRequest(request.id)}
                                    />
                                ))}
                            </div>
                        )}
                    </>
                )}

                {/* Sent Requests Tab */}
                {activeTab === "sent" && (
                    <>
                        {loading ? (
                            <div className="loading-state">Loading requests...</div>
                        ) : sentRequests.length === 0 ? (
                            <div className="empty-state">
                                <span className="empty-icon">📤</span>
                                <h3>No sent requests</h3>
                                <p>You haven't sent any friend requests.</p>
                                <button
                                    className="add-friend-btn"
                                    onClick={() => setShowAddModal(true)}
                                >
                                    + Add Friend
                                </button>
                            </div>
                        ) : (
                            <div className="requests-list">
                                {sentRequests.map((request) => (
                                    <FriendRequestCard
                                        key={request.id}
                                        request={request}
                                        type="sent"
                                        onCancel={() => handleCancelRequest(request.id)}
                                    />
                                ))}
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Add Friend Modal */}
            {showAddModal && (
                <AddFriendModal
                    onClose={() => setShowAddModal(false)}
                    onSendRequest={handleSendRequest}
                />
            )}
        </div>
    );
};

export default Friends;