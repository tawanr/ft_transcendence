import { updateUserNav } from "./utils.js";
import * as constants from "./constants.js";

const signupForm = document.getElementById("signupForm");
const submitBtn = document.getElementById("submitBtn");

signupForm.addEventListener("submit", (e) => {
    e.preventDefault();

    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;

    signUpAccount(username, password);
    // localStorage["username"] = username;
    // updateUserNav();
});

function signUpAccount(username, password) {
    const api_url = constants.BACKEND_HOST + "/account/register/";
    // TODO: Error handling
    fetch(api_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            username,
            password,
        }),
    }).then((response) => {
        if (response.status === 200) {
            history.pushState({}, "", "/login");
            window.dispatchEvent(new PopStateEvent("popstate"));
        }
        return response.json();
    });
}
