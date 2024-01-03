export function updateUserNav() {
    const username = localStorage.getItem("username");
    const navAuth = document.getElementById("navAuth");
    const navLoggedIn = document.getElementById("navLoggedIn");
    if (username == "") {
        navAuth.classList.remove("d-none");
        navLoggedIn.classList.add("d-none");
    } else {
        navAuth.classList.add("d-none");
        navLoggedIn.querySelector("a").innerText = username;
        navLoggedIn.classList.remove("d-none");
    }
}