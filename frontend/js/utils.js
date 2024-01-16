export function updateUserNav() {
    /**
     * Update the navbar with the current user if logged in
     * and there is a username in localStorage. Otherwise,
     * show the login and signup links.
     */
    const username = localStorage.getItem("username");
    const navAuth = document.getElementById("navAuth");
    const navLoggedIn = document.getElementById("navLoggedIn");
    if (!username) {
        navAuth.classList.remove("d-none");
        navLoggedIn.classList.add("d-none");
    } else {
        navAuth.classList.add("d-none");
        navLoggedIn.querySelector("a").innerText = username;
        navLoggedIn.classList.remove("d-none");
    }
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
