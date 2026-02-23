import React, { useEffect, useState } from 'react';

const icons = {
    success: "✅",
    error: "❌",
    info: "ℹ️",
    warning: "⚠️",
};

const Toast = ({ id, message, type, duration, onClose }) => {
    const [ existing, setExisting ] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setExisting(true);
            setTimeout(onClose, 300);
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    const handleClose = () => {
        setExisting(true);
        setTimeout(onClose, 300);
    };

    return (
        <div className={`toast toast-${type} ${existing ? "toast-exist" : ""}`}>
            <span className="toast-icon">{icons[type]}</span>
            <span className="toast-message">{message}</span>
            <button className="toast-close" onClick={handleClose}>
                ✕
            </button>
        </div>
    );
};

export default Toast;