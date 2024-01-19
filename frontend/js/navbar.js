import { initUser, updateUserNav } from "./utils.js";
import * as constants from "./constants.js";

const logoutBtn = document.getElementById("logoutBtn");

logoutBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    const api_url = constants.BACKEND_HOST + "/account/logout/";
    await fetch(api_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + localStorage.getItem("token"),
        },
    }).then((response) => {
        if (response.status === 200) {
            console.log("Logged out successfully");
        } else {
            console.error("Failed to log out", response.json());
            return;
        }
    });
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    updateUserNav();
});

function checkLoggedIn() {
    initUser();
}

checkLoggedIn();
