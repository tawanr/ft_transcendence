import * as constants from "./constants.js";


export async function initUser() {
    /** 
     * Initialize the state of the user.
     * Check localStorage whether there's a saved token
     * Then fetch the user data from the backend
     */
    const token = localStorage.getItem("token");
    const username = await fetchUserData(token);
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
        navLoggedIn.querySelector("button").innerText = username;
        navLoggedIn.classList.remove("d-none");
    }
}

export async function fetchUserData(token) {
    /**
     * Fetch user data from the backend
     */
    if (!token) {
        localStorage.removeItem("token");
        return null;
    }
    const api_url = constants.BACKEND_HOST + "/account/user/";
    return await fetch(api_url, {
        headers: {
            Authorization: "Bearer " + token,
        },
    })
        .then((response) => {
            // TODO: Refresh token
            if (response.status === 401) {
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
