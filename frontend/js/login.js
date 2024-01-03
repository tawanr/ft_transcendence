import { updateUserNav } from "./utils.js";

const loginForm = document.getElementById("loginForm");

loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    
    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;

    // TODO: Needs sanitization
    localStorage["username"] = username;
    updateUserNav();
})