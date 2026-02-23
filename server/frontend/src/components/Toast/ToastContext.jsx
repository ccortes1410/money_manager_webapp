import React, { createContext, useContext, useState, useCallback } from 'react';
import ToastContainer from './ToastContainer';

const ToastContext = createContext(null);

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error("useToast must be used within a ToastProvider");
    }
    return context;
};

export const ToastProvider = ({ children }) => {
    const [ toasts, setToasts ] = useState([]);

    const addToast = useCallback((message, type = "info", duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts((prev) => [...prev, { id, message, type, duration }]);
    }, []);

    const removeToast = useCallback((id) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);
    
    const toast = {
        success: (msg, duration) => addToast(msg, "success", duration),
        error: (msg, duration) => addToast(msg, "error", duration),
        info: (msg, duration) => addToast(msg, "info", duration),
        warning: (msg, duration) => addToast(msg, "warning", duration),
    };

    return (
        <ToastContext.Provider value={toast}>
            {children}
            <ToastContainer toasts={toasts} removeToast={removeToast} />
        </ToastContext.Provider>
    );
};

