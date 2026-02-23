import React, { useState, useEffect } from 'react';
import { AuthContext } from './AuthContext';
import { apiFetch } from './utils/csrf';

const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Check session on mount (persists across refresh)
    useEffect(() => {
        const checkSession = async () => {
            try {
                const res = await apiFetch("/djangoapp/session", {
                    method: 'GET',
                });

                if (res.ok) {
                    const data = await res.json();
                    if (data.is_authenticated) {
                        setUser(data);
                    } else { 
                        setUser(null);
                    }
                } else {
                    setUser(null);
                }
            } catch (error) {
                console.error("Session check failed:", error);
                setUser(null);
            } finally {
                setLoading(false);
            }
        };

        checkSession();
    }, []);

    const logout = async () => {
        try {
            await apiFetch("/djangoapp/logout", {
                method: 'POST',
            });
        } catch (error) {
            console.error("Logout error:", error);
        } finally {
            setUser(null);
        }
    };

    return (
        <AuthContext.Provider value={{ user, setUser, loading, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthProvider;