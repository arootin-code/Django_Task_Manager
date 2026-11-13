const TOKEN_KEY = "access_token";
const REFRESH_KEY = "refresh_token";
const USERNAME_KEY = "username";

function getAccessToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY);
}

function setTokens(access, refresh, username) {
    localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    if (username) localStorage.setItem(USERNAME_KEY, username);
}

function clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USERNAME_KEY);
}

function requireAuth() {
    if (!getAccessToken()) {
        window.location.href = "/login/";
        return false;
    }
    return true;
}

document.addEventListener("DOMContentLoaded", () => {
    const usernameEl = document.getElementById("nav-username");
    if (usernameEl) {
        const username = localStorage.getItem(USERNAME_KEY);
        if (username) usernameEl.textContent = username;
    }

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            clearTokens();
            window.location.href = "/login/";
        });
    }
});