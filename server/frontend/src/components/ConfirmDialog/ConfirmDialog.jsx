import React from 'react';
import './ConfirmDialog.css';

const ConfirmDialog = ({ title, message, confirmText = "Delete", cancelText = "Cancel", onConfirm, onCancel, danger = true }) => {
    return (
        <div className="confirm-overlay" onClick={onCancel}>
            <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
                <div className="confirm-icon">{danger ? "🗑️" : "❓"}</div>
                <h3>{title}</h3>
                <p>{message}</p>
                <div className="confirm-actions">
                    <button className="confirm-cancel-btn" onClick={onCancel}>
                        {cancelText}
                    </button>
                    <button
                        className={`confirm-action-btn ${danger ? "danger" : ""}`}
                        onClick={onConfirm}
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ConfirmDialog;