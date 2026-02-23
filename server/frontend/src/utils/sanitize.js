// Removes potentially dagnerous characters from user input
export const sanitizeInput = (str) => {
    if (typeof str !== "string") return str;
    return str.replace(/[<>{}]/g, "").trim();
};

// Sanitize an object's string values (useful for form data)
export const sanitizeFormData = (data) => {
    const sanitized = {};
    for (const [key, value] of Object.entries(data)) {
        sanitized[key] = typeof value === "string" ? sanitizeInput(value) : value;
    }
    return sanitized;
};

// Validate email format
export const isValidEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

// Validate password strength
export const validatePassword = (password) => {
    const errors = [];
    if (password.length < 8) errors.push("Must be at least 8 characters");
    if (!/[A-Z]/.test(password)) errors.push("Include at least one uppercase letter");
    if ( !/[0-9]/.test(password)) errors.push("Include at least one number");
    return errors;
};