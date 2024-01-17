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
    const navAuth = document.getElementById("navAuth");
    const navLoggedIn = document.getElementById("navLoggedIn");
    if (!token || !username) {
        navAuth.classList.remove("d-none");
        navLoggedIn.classList.add("d-none");
        console.log(navLoggedIn.classList);
    } else {
        navAuth.classList.add("d-none");
        const navUserMenu = document.getElementById("navUserDropdown");
        console.log(navUserMenu.innerHTML);
        navUserMenu.innerHTML = `
        <div class="flex-col profileAvatar">
            <img src="static/42_Logo.png" class="w-100 h-100 object-fit-cover my-auto" />
        </div>
        <div class="flex-col h-100 my-auto mx-2">${username}</div>
        `;
        console.log(navUserMenu);
        navLoggedIn.classList.remove("d-none");
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
            return data.username;
        });
}

export async function refreshUserToken() {
    /**
     * Refresh the user token, it should send a request to the endpoint
     * with cookies retrieved previously.
     */
    const api_url = constants.BACKEND_HOST + "/account/refresh/";
    await fetch(api_url, {
        method: "POST",
        credentials: "include",
    }).then((response) => response.json()).then((data) => {
        if (!data.access_token) {
            localStorage.removeItem("token");
            return false;
        }
        localStorage["token"] = data.access_token;
        return true;
    })
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
