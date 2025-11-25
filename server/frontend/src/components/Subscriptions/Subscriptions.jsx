import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Subscriptions.css';
import '../assets/style.css';
import Sidebar from '../Sidebar/Sidebar';

const Subscriptions = () => {
    const [ amountInput, setAmountInput ] = useState("");
    const [ dateInput, setDateInput ] = useState("");
    const [ descriptionInput, setDescriptionInput ] = useState("");
    const [ categoryInput, setCategoryInput ] = useState("");
    const [ frequencyInput, setFrequencyInput ] = useState("monthly");
    const [ activeInput, setActiveInput ] = useState(false);
    const [ subscriptions, setSubscriptions ] = useState([]);
    const [ collapsed, setCollapsed ] = useState(true);
    const [ user, setUser ] = useState(null);
    const [ selectedSubs, setSelectedSubs ] = useState([]);

    const FREQUENCY_OPTIONS = [
        { value: "daily", label: "Daily" },
        { value: "weekly", label: "Weekly" },
        { value: "monthly", label: "Monthly" },
        { value: "yearly", label: "Yearly" },
    ];

    const getToday = () => {
        const today = new Date();
        return today.toISOString().split('T')[0];
    }

    const subscription_url = "/djangoapp/subscriptions";
    // const addSubscription_url = "/djangoapp/addSubscription";

    const navigate = useNavigate();

    const get_subscriptions = async () => {
        try {
            const response = await fetch(subscription_url, {
                method: "GET",
                credentials: "include",
            });

            const data = await response.json();

            if (data.subscriptions && Array.isArray(data.subscriptions)) {
                setSubscriptions(data.subscriptions);
                setUser(data.user);
                // if (data.subscriptions.length > 0) {
                //     setSelectedSubscriptionId(data.subscriptions[0].id);
                // }
            }
        } catch (error) {
            alert("Error fetching subscriptions");
            setSubscriptions([]);
            setUser(null);
            setSelectedSubs([]);
            console.error(error);
        }
    }

    const handleAddSubscription = async () => {
        const amount = amountInput;
        const date = dateInput || getToday();
        const description = descriptionInput;
        const category = categoryInput;
        const frequency = frequencyInput;
        const active = activeInput;

        const newSubscription = {
            amount: parseFloat(amount),
            due_date: date,
            description: description,
            category: category,
            frequency: frequency,
            active: active,
        };

        try {
            const response = await fetch(subscription_url, {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(newSubscription),
            });

            const result = await response.json();
            if (response.ok || result.ok) {
                get_subscriptions();
                setAmountInput("");
                setDateInput("");
                setDescriptionInput("");
                setCategoryInput("");
                setFrequencyInput("");
                setActiveInput(false);
            } else {
                alert("Error adding subscription");
            }
        } catch (error) {
            alert("Error adding subscription");
            console.error(error);
        }
    }

    const handleDeleteSubscription = async (subscriptionId) => {
        if (selectedSubs === 0) return;

        const delete_url = `/djangoapp/subscriptions/${subscriptionId}/delete/`;
        try {
            const response = await fetch(delete_url, {
                method: "DELETE",
                credentials: "include",
                body: JSON.stringify({ id: subscriptionId }),
            });
            if (!response.ok) {
                throw new Error("Failed to delete subscription");
            }
            alert("Subscription deleted successfully");
            window.location.href = '/subscriptions'; // Redirect to subscriptions page
        } catch (error) {
            alert("Error deleting subscriptions: " + error.message);
            console.error(error);
        }
    }

    const handleSelect = (id) => {
        setSelectedSubs(prev =>
            prev.includes(id) ? 
            prev.filter(sId => sId !== id) :
            [...prev, id]
        )
    }

    useEffect(() => {
        get_subscriptions();
    }, []);

    const handleToggleActive = async () => {
        if (selectedSubs.length === 0) return;

        const shouldActivate = subscriptions
            .filter((s) => selectedSubs.includes(s.id))
            .some((s) => !s.active);

        const updated = subscriptions.map((s) => 
            selectedSubs.includes(s.id) ? { ...s, active: shouldActivate} : s  
        );

        setSubscriptions(updated);

        try {
            const update_url = `/djangoapp/subscriptions/${}`
            await fetch()
        }
    }

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate('/');
        }
    }, [user]);

    useEffect(() => {
        setActiveInput(data.active)
    },[])

    return (
        <div style={{ display: 'flex', width: '100vw', height: '100vh', overflow: 'hidden' }}>
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
            <div className="subscriptions-container">
                <div className="subscriptions-header">
                    <h1 style={{ color: '#fff' }}>Subscriptions</h1>
                    <div className="active-user">
                        <p style={{ marginTop: '10px' }}>{user ? user.username : "Not Logged In"}</p>
                    </div>
                </div>
            
                <div className="input-header">
                    <div>
                        <input
                            type="number"
                            placeholder='Amount'
                            style={{ marginTop: '10px', marginLeft: '10px' }}
                            value={amountInput}
                            onChange={(e) => setAmountInput(e.target.value)}
                        />
                        <input 
                            type="text"
                            placeholder='Description'
                            style={{ marginTop: '10px', marginLeft: '10px' }}
                            value={descriptionInput}
                            onChange={(e) => setDescriptionInput(e.target.value)}
                        />
                        <input 
                            type="text"
                            placeholder='Category'
                            style={{ marginTop: '10px', marginLeft: '10px' }}
                            value={categoryInput}
                            onChange={(e) => setCategoryInput(e.target.value)}
                        />
                        <input 
                            type="date"
                            style={{ marginTop: '10px', marginLeft: '10px' }}
                            value={dateInput}
                            onChange={(e) => setDateInput(e.target.value)}
                        />
                        <select
                            name="frequency"
                            value={frequencyInput}
                            onChange={(e) => setFrequencyInput(e.target.value)}
                        >
                            {FREQUENCY_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            ))}
                        </select>
                        <input
                            type="checkbox"
                            name="active"
                            value={activeInput}
                            onChange={(e) => setActiveInput(true)}
                        />
                        <button
                            className="button-add"
                            onClick={handleAddSubscription}
                        >
                            Add Subscription
                        </button>
                        <button
                            className="button-delete"
                            onClick={() => handleDeleteSubscription(selectedSubs)}
                            style={{ marginLeft: '10px' }}
                        >
                            Delete Subscription
                        </button>
                    </div>
                </div>
            <div className="subscription-grid">
                {Array.isArray(subscriptions) && subscriptions.length > 0 ? (
                        subscriptions.map((s) => (                    
                        <div 
                            className={`subscription-card ${selectedSubs.includes(s.id) ? "selected" : ""}`}
                            key={s.id}
                            onClick={() => handleSelect(s.id)}
                        >
                            <h4>{s.description}</h4>
                            <p>${s.amount}</p>
                            <p>Due: {s.due_date}</p>
                            <div
                                className={`status-indicator ${s.active ? "active" : "inactive"}`}
                                title={s.active ? "Active" : "Inactive"}
                            >
                                {s.active ? "Active" : "Inactive"}
                            </div>
                        </div>
                
                ))
        ) : (
            <p>No subscriptions found.</p>
        )}
        </div>
            </div>
        </div>
    );
}

export default Subscriptions;