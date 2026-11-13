const AVATAR_COLORS = [
    "#3b82f6",
    "#22c55e",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#ec4899",
    "#06b6d4",
    "#f97316",
];

export function getAvatarColor(username = "") {
    if (!username) return AVATAR_COLORS[0];
    const index = username.charCodeAt(0) % AVATAR_COLORS.length;
    return AVATAR_COLORS[index];
}

export function getInitials(user) {
    if (!user) return "?";
    if (user.first_name && user.last_name) {
        return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    return (user.username || "?")[0].toUpperCase();
}

export function getDisplayName(user) {
    if (!user) return "Unknown";
    if (user.first_name || user.last_name) {
        return `${user.first_name || ""} ${user.last_name || ""}`.trim();
    }
    return user.username || "Unknown";
}

export function formatCurrency(val) {
    const num = parseFloat(val);
    if (isNaN(num)) return "$0.00";
    return `$${num.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })}`;
}
