import React, { useState, useEffect } from 'react';

const CreateSharedBudgetModal = ({ onClose, onSave }) => {
    const [ formData, setFormData ] = useState({
        name: "",
        description: "",
        total_amount: "",
        category: "",
        start_date: new Date().toISOString().split('T')[0],
        end_date: "",
        split_type: "equal",
    })
    const [ friends, setFriends ] = useState([]);
    const [ selectedFriends, setSelectedFriends ] = useState([]);
    const [ errors, setErrors ] = useState({});
    const [ loadingFriends, setLoadingFriends ] = useState(true);

    const categories = [
        "Housing", "Food", "Transportation", "Entertainment",
        "Travel", "Utilities", "Shopping", "Health", "Other",
    ];

    useEffect(() => {
        fetchFriends();
    }, []);

    const fetchFriends = async () => {
        try {
            const res = await fetch("/djangoapp/friends", {
                credentials: 'include',
            });
            const data = await res.json();
            
            if (data.friends) {
                setFriends(Array.isArray(data.friends) ? data.friends : []);
            }
        } catch (error) {
            console.error("Error fetching friends:", error);
        } finally {
            setLoadingFriends(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value}));
        if (errors[name]) {
            setErrors((prev) => ({ ...prev, [name]: ""}));
        }
    };

    const toggleFriend = (friendId) => {
        setSelectedFriends((prev) => {
            if (prev.includes(friendId)) {
                return prev.filter((id) => id !== friendId);
            }
            return [...prev, friendId];
        });
    };

    const validate = () => {
        const newErrors = {};
        if (!formData.name.trim()) newErrors.name = "Name is required";
        if (!formData.total_amount || parseFloat(formData.total_amount) <= 0) {
            newErrors.total_amount = "Enter a valid amount";
        }
        if (!formData.start_date) newErrors.start_date = "Start date is required";
        if (!formData.end_date) newErrors.end_date = "End date is required";
        if (formData.start_date && formData.end_date && formData.end_date < formData.start_date) {
            newErrors.end_date = "End date must be after start date";
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!validate()) return;

        onSave({
            ...formData,
            total_amount: parseFloat(formData.total_amount),
            invite_friends: selectedFriends.map((id) => ({
                user_id: id,
                role: "editor",
            })),
        });
    };

    const setThisMonthPeriod = () => {
        const now = new Date();
        const start = new Date(now.getFullYear(), now.getMonth(), 1);
        const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        setFormData((prev) => ({
            ...prev,
            start_data: start.toISOString().split('T')[0],
            end_date: end.toISOString().split('T')[0],
        }));
    };

    const getAvatarColor = (username) => {
        const colors = [
            "#3b82f6",
            "#22c55e",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
            "#ec4899",
        ];
        if (!username) return colors[0];
        return colors[username.charAt(0) % colors.length];
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content sb-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Create Shared Budget</h2>
                    <button className="modal-close-btn" onClick={onClose}>×</button>
                </div>

                <form onSubmit={handleSubmit} className="sb-modal-form">
                    {/* Name */}
                    <div className="sb-form-group">
                        <label>Budget Name *</label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            placeholder="e.g., Apartment Expenses"
                            className={errors.name ? "error" : ""}
                        />
                        {errors.name && <span className="sb-error">{errors.name}</span>}
                    </div>

                    {/* Description */}
                    <div className="sb-form-group">
                        <label>Description</label>
                        <textarea
                            name="description"
                            value={formData.description}
                            onChange={handleChange}
                            placeholder="What is this budget for?"
                            rows="2"
                        />
                    </div>

                    {/* Amount & Category */}
                    <div className="sb-form-row">
                        <div className="sb-form-group">
                            <label>Total Amount</label>
                            <input
                                type="number"
                                name="total_amount"
                                value={formData.total_amount}
                                onChange={handleChange}
                                placeholder="0.00"
                                step="0.01"
                                min="0"
                                className={errors.total_amount ? "error" : ""}
                            />
                            {errors.total_amount && (
                                <span className="sb-error">{errors.total_amount}</span>
                            )}
                        </div>
                        <div className="sb-form-group">
                            <label>Category</label>
                            <select 
                                name="category"
                                value={formData.category}
                                onChange={handleChange}
                            >
                                <option value="">Select category</option>
                                {categories.map((cat) => (
                                    <option key={cat} value={cat}>{cat}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Period */}
                    <div className="sb-form-group">
                        <label>Period *</label>
                        <div className="sb-period-presets">
                            <button
                                type="button"
                                className="sb-preset-btn"
                                onClick={setThisMonthPeriod}
                            >
                                This Month
                            </button>
                        </div>
                    </div>

                    <div className="sb-form-row">
                        <div className="sb-form-group">
                            <label>Start Date *</label>
                            <input
                                type="date"
                                name="start_date"
                                value={formData.start_date}
                                onChange={handleChange}
                                className={errors.start_date ? "error" : ""}
                            />
                            {errors.start_date && <span className="sb-error">{errors.start_date}</span>}
                        </div>
                        <div className="sb-form-group">
                            <label>End Date *</label>
                            <input
                                type="date"
                                name="end_date"
                                value={formData.end_date}
                                onChange={handleChange}
                                className={errors.end_date ? "error" : ""}
                            />
                            {errors.end_date && <span className="sb-error">{errors.end_date}</span>}
                        </div>
                    </div>

                    {/* Split Type */}
                    <div className="sb-form-group">
                        <label>Default Split Type</label>
                        <select 
                            name="split_type"
                            value={formData.split_type}
                            onChange={handleChange}
                        >
                            <option value="equal">Equal Split</option>
                            <option value="percentage">By Percentage</option>
                            <option value="custom">Custom Amounts</option>
                        </select>
                    </div>

                    {/* Invite Friends */}
                    <div className="sb-form-group">
                        <label>Invite Friends ({selectedFriends.length} selected)</label>
                        <div className="sb-friends-list">
                            {loadingFriends ? (
                                <p className="sb-loading-text">Loading friends...</p>
                            ) : friends.length === 0 ? (
                                <p className="sb-empty-text">
                                    No friends to invite. Add friends first!
                                </p>
                            ) : (
                                friends.map((friend) => (
                                    <div
                                        key={friend.id}
                                        className={`sb-friend-option ${
                                            selectedFriends.includes(friend.id) ? "selected" : ""
                                        }`}
                                        onClick={() => toggleFriend(friend.id)}
                                    >
                                        <div 
                                            className="sb-friend-avatar"
                                            style={{
                                                backgroundColor: getAvatarColor(friend.username),
                                            }}
                                        >
                                            {friend.username?.slice(0, 2).toUpperCase()}
                                        </div>
                                        <span className="sb-friend-name">
                                            {friend.first_name || friend.username}
                                        </span>
                                        <span className="sb-friend-check">
                                            {selectedFriends.includes(friend.id) ? "✓" : "+"}
                                        </span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="sb-modal-actions">
                        <button
                            type="button"
                            className="sb-cancel-btn"
                            onClick={onClose}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="sb-save-btn"
                        >
                            Create Budget
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreateSharedBudgetModal;