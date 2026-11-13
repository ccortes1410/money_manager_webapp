import React, { useEffect, useState } from 'react';

const icons = {
    success: "✅",
    error: "❌",
    info: "ℹ️",
    warning: "⚠️",
};

const Toast = ({ id, message, type, duration, onClose }) => {
    const [ exiting, setExiting ] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setExiting(true);
            setTimeout(onClose, 300);
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    const handleClose = () => {
        setExiting(true);
        setTimeout(onClose, 300);
    };

    return (
        <div className={`toast toast-${type} ${exiting ? "toast-exit" : ""}`}>
            <span className="toast-icon">{icons[type]}</span>
            <span className="toast-message">{message}</span>
            <button className="toast-close" onClick={handleClose}>
                ✕
            </button>
        </div>
    );
};

export default Toast;