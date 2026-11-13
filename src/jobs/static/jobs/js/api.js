async function apiFetch(path, options = {}) {
    let access = getAccessToken();

    if (!access) {
        window.location.href = "/login/";
        throw new Error("No access token");
    }

    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
        Authorization: `Bearer ${access}`,
    };

    let response = await fetch(path, { ...options, headers });

    if (response.status === 401) {
        const refreshed = await tryRefresh();
        if (refreshed) {
            headers.Authorization = `Bearer ${getAccessToken()}`;
            response = await fetch(path, { ...options, headers });
        } else {
            clearTokens();
            window.location.href = "/login/";
            throw new Error("Session expired");
        }
    }

    return response;
}

async function tryRefresh() {
    const refresh = getRefreshToken();
    if (!refresh) return false;

    try {
        const res = await fetch("/api/auth/refresh/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        localStorage.setItem("access_token", data.access);
        return true;
    } catch {
        return false;
    }
}

async function apiJSON(path, options = {}) {
    const res = await apiFetch(path, options);
    if (res.status === 204) return null;
    const data = await res.json().catch(() => null);
    if (!res.ok) {
        const msg = (data && (data.detail || JSON.stringify(data))) || `HTTP ${res.status}`;
        throw new Error(msg);
    }
    return data;
}