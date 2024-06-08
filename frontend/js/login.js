import { initUser, updateUserNav } from "./utils.js";
import * as constants from "./constants.js";

const loginForm = document.getElementById("loginUser");

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;

    // TODO: Needs sanitization
    await signInAccount(username, password);
    await initUser();
});

const login42 = document.getElementById("login42");

login42.addEventListener("click", async (e) => {
    e.preventDefault();

    // call 42 login api
    await signIn42();
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
                history.pushState({}, "", "/");
                window.dispatchEvent(new PopStateEvent("popstate"));
            }
            return response.json();
        })
        .then((data) => {
            localStorage["token"] = data.access_token;
        });
}

async function signIn42() {
    // TODO: Implement 42 login
    const api_url = constants.BACKEND_HOST + "/account/oauth42/";
    const response = await fetch(api_url)

    console.log(response)
    // .then((response) => {
    //     if (response.status === 200) {
    //         history.pushState({}, "", "/");
    //         window.dispatchEvent(new PopStateEvent("popstate"));
    //     }
    //     return response.json();
    // })
    // .then((data) => {
    //     localStorage["token"] = data.access_token;
    // });
}
