import React from 'react';
import "./ErrorBoundary.css";

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null,
        };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("ErrorBoundary caught:", error, errorInfo);
        this.setState({ errorInfo });

        // TODO: Send to error tracking service (e.g., Sentry)
        // LogErrorToService(error, errorInfo);
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null, errorInfo: null });
    };

    handleReload = () => {
        window.location.reload();
    };

    handleGoHome = () => {
        window.location.href = "/";
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="error-boundary">
                    <div className="error-boundary-content">
                        <div className="error-bounding-icon">⚠️</div>
                        <h1>Something went wrong</h1>
                        <p>
                            An unexpected error ocurred. Don't worry - your data is safe.
                        </p>

                        {process.env.NODE_ENV === "development" && this.state.error && (
                            <details className="error-boundary-details">
                                <summary>Error Details</summary>
                                <pre>{this.state.error.toString()}</pre>
                                <pre>{this.state.errorInfo?.componentStack}</pre>
                            </details>
                        )}

                        <div className="error-boundary-actions">
                            <button
                                className="eb-btn-primary"
                                onClick={this.handleReload}
                            >
                                🔄 Refresh Page
                            </button>
                            <button
                                className="eb-btn-secondary"
                                onClick={this.handleGoHome}
                            >
                                🏠 Go Home
                            </button>
                        </div>
                    </div>
                </div>
            );
        }
        
        return this.props.children;
    }
}

export default ErrorBoundary;