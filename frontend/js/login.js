import { initUser, updateUserNav } from "./utils.js";
import * as constants from "./constants.js";

const loginForm = document.getElementById("loginForm");

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;

    // TODO: Needs sanitization
    await signInAccount(username, password);
    await initUser();
});

async function signInAccount(username, password) {
    const api_url = constants.BACKEND_HOST + "/account/login/";
    await fetch(api_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
            username,
            password,
        }),
    })
        .then((response) => {
            if (response.status === 200) {
                console.log("Account logged in successfully");
                history.pushState({}, "", "/");
                window.dispatchEvent(new PopStateEvent("popstate"));
            }
            return response.json();
        })
        .then((data) => {
            localStorage["token"] = data.access_token;
        });
}
