import { updateUserNav } from "./utils.js";

const signupForm = document.getElementById("signupForm");

signupForm.addEventListener("submit", (e) => {
    e.preventDefault();
    
    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;

    // TODO: Needs sanitization
    // localStorage["username"] = username;
    // updateUserNav();
})
