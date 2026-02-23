import React from "react";
import Toast from "./Toast";
import './Toast.css';

const ToastContainer = ({ toasts, removeToast }) => {
    return (
        <div className="toast-container">
            {toasts.map((t) => (
                <Toast
                    key={t.id}
                    id={t.id}
                    message={t.message}
                    type={t.type}
                    duration={t.duration}
                    onClose={() => removeToast(t.id)}
                />
            ))}
        </div>
    );
};

export default ToastContainer;