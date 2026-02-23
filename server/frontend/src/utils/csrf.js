export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
                break;
            }
        }
    }
    return cookieValue;
}

export function getCSRFToken() {
    return getCookie("csrftoken");
}

const nativeFetch = window.fetch.bind(window);
// Wrapper around fetch that automatically includes
// credentials, CSRF token, and Content-Type headers.

export async function apiFetch(url, options = {}) {
    const method = options.method || 'GET';
    const isFormData = options.body instanceof FormData;

    const headers = {
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
        'X-CSRFToken': getCSRFToken(),
        ...(options.headers || {}),
    };

    try {
        const response = await nativeFetch(url, {
            method,
            credentials: 'include',
            headers,
            ...(options.body ? { body: options.body } : {}),
        });

        return response;
    } catch (error) {
        console.error(`apiFetch ${method} ${url} failed:`, error);
        throw error;
    }
}