import React from 'react';
import './LoadingScreen.css';

const LoadingScreen = ({ message = "Loading..." }) => {
    return (
        <div className="loading-screen">
            <div className="loading-screen-content">
                <div className="loading-screen-logo">💰</div>
                <div className="loading-screen-spinner" />
                <span className="loading-screen-text">{message}</span>
            </div>
        </div>
    );
};

export default LoadingScreen;