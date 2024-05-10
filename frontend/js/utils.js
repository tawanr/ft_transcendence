import * as constants from "./constants.js";

export async function initUser() {
    /**
     * Initialize the state of the user.
     * Check localStorage whether there's a saved token
     * Then fetch the user data from the backend
     */
    const token = localStorage.getItem("token");
    const username = await fetchUserData(token).catch((error) => {
        return fetchUserData(localStorage.getItem("token"));
    });
    if (username) {
        localStorage["username"] = username;
    } else {
        localStorage.removeItem("username");
    }
    updateUserNav();
}

export function updateUserNav() {
    /**
     * Update the navbar with the current user if logged in
     * and there is a username in localStorage. Otherwise,
     * show the login and signup links.
     */
    const token = localStorage.getItem("token");
    const username = localStorage.getItem("username");
    const userAvatar = localStorage.getItem("userAvatar");
    const navAuth = document.getElementById("navAuth");
    const navTour = document.getElementById("navTour");
    const navLoggedIn = document.getElementById("navLoggedIn");
    if (!token || !username) {
        localStorage.removeItem("userAvatar");
        navAuth.classList.remove("d-none");
        navLoggedIn.classList.add("d-none");
        navTour.classList.add("d-none");
    } else {
        navAuth.classList.add("d-none");
        const navUserMenu = document.getElementById("navUserDropdown");
        navUserMenu.innerHTML = `
        <div class="flex-col profileAvatar">
            <img src="${
                userAvatar ? userAvatar : constants.USER_AVATAR
            }" class="w-100 h-100 object-fit-cover my-auto" />
        </div>
        <div class="flex-col h-100 my-auto mx-2">${username}</div>
        `;
        navLoggedIn.classList.remove("d-none");
        navTour.classList.remove("d-none");
    }
}

export async function fetchUserData(token) {
    /**
     * Fetch user data from the backend.
     * Returns username or null.
     */
    if (!token) {
        localStorage.removeItem("token");
        return null;
    }
    const api_url = constants.BACKEND_HOST + "/account/user/";
    return fetch(api_url, {
        headers: {
            Authorization: "Bearer " + token,
        },
    })
        .then(async (response) => {
            if (response.status === 401) {
                await refreshUserToken();
                throw new Error("Token expired");
            } else if (response.status !== 200) {
                localStorage.removeItem("token");
                return null;
            }
            return response.json();
        })
        .then((data) => {
            if (!data) {
                return null;
            }
            if (data.avatar && data.avatar.length > 0) {
                localStorage["userAvatar"] = constants.BACKEND_HOST + data.avatar;
            } else {
                localStorage.removeItem("userAvatar");
            }
            return data.username;
        });
}

export async function refreshUserToken() {
    /**
     * Refresh the user token, it should send a request to the endpoint
     * with cookies retrieved previously.
     */
    const api_url = constants.BACKEND_HOST + "/account/refresh/";
    const token = localStorage.getItem("token");
    if (!token) {
        return false;
    }
    const expire = parseJwt(token).exp;
    if (expire - 5 > Date.now() / 1000) {
        return false;
    }
    await fetch(api_url, {
        method: "POST",
        credentials: "include",
    })
        .then((response) => response.json())
        .then((data) => {
            if (!data.access_token) {
                localStorage.removeItem("token");
                return false;
            }
            localStorage["token"] = data.access_token;
            return true;
        });
}

export function updateNavLinks(route) {
    /**
     * Update the navbar to show the active page according
     * to the `navLink` property of the route.
     */
    const navLink = document.querySelector(".nav-link.active");
    if (navLink) {
        navLink.classList.remove("active");
    }
    if ("navLink" in route) {
        document.getElementById(route.navLink).classList.add("active");
    }
}

export function fetchHTML(filePath) {
    const baseStyle = `
        <link
            href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
            rel="stylesheet"
            integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"
            crossorigin="anonymous"
        />
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
        <link rel="stylesheet" href="/css/index.css" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
        <link
            href="https://fonts.googleapis.com/css2?family=Kanit:wght@400&display=swap"
            rel="stylesheet"
        />
    `;
    return fetch(filePath)
        .then((response) => {
            return response.text();
        })
        .then((data) => {
            return baseStyle + data;
        });
}

export function parseJwt(token) {
    var base64Url = token.split(".")[1];
    var base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    var jsonPayload = decodeURIComponent(
        window
            .atob(base64)
            .split("")
            .map(function (c) {
                return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
            })
            .join("")
    );

    return JSON.parse(jsonPayload);
}

export function getUserToken() {
    refreshUserToken();
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.replace("/login");
        return;
    }
    return token;
}
