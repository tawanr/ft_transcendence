import { initUser, updateUserNav } from "./utils.js";
import * as constants from "./constants.js";

const logoutBtn = document.getElementById("logoutBtn");
let hasNotifications = false;

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
        if (response.status !== 200) {
            console.error("Failed to log out", response.json());
        }
    });
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    updateUserNav();
});

/**
 * @typedef {Object} Notification
 * @property {number} notification
 * @property {string} isRead
 */

function getNotificationText(type) {
    const textMapping = {
        private_chat: "Someone sent you a message",
        tour_chat: "There's a new message in the tournament chat",
        friend_invite: "Someone sent you a friend invite",
        game_invite: "Someone sent you a game invite",
        tour_invite: "Someone sent you a tournament invite",
        game_start: "A game you're in has started",
        tour_round: "The tournament you're in has started a new round",
    };
    return textMapping[type];
}

function getNotificationLink(type) {
    const linkMapping = {
        private_chat: "/",
        tour_chat: "/tournament",
        friend_invite: "/",
        game_invite: "/game",
        tour_invite: "/tournament",
        game_start: "/game",
        tour_round: "/tournament",
    };
    return linkMapping[type];
}

/**
 *
 * @param {Notification} notification
 */
function addNotification(notification) {
    const notificationList = document.querySelector("#navNotifications ul");
    const notiObject = document.createElement("li");
    notiObject.classList.add("dropdown-item");
    const notiText = getNotificationText(notification.notification);
    const notiLink = getNotificationLink(notification.notification);
    if (!notiText) {
        return;
    }
    const notiLinkObj = document.createElement("div");
    notiLinkObj.onclick = () => {
        window.location.replace(notiLink);
    };
    notiLinkObj.innerHTML = `
        <div class="d-flex flex-row justify-content-between align-items-center notificationItem" style="min-width: 20rem; min-height: 2.5rem">
            <div class="flex-column" style="width: 10px; height: 10px">
                <span class="position-absolute p-1 bg-danger border border-light rounded-circle ${
                    notification.isRead ? "d-none" : ""
                }"></span>
            </div>
            <div class="d-flex flex-column">${notiText}</span>
        </div>
    `;
    notiObject.appendChild(notiLinkObj);
    notificationList.prepend(notiObject);
    if (!notification.isRead) {
        hasNotifications = true;
        const notificationAlert = document.getElementById("notiNewAlert");
        notificationAlert.classList.remove("d-none");
    }
}

/**
 *
 * @param {Notification} notifications
 */
function renderNotifications(notifications) {
    const notificationList = document.querySelector("#navNotifications ul");
    const newList = document.createElement("ul");
    newList.classList.add("dropdown-menu");
    newList.classList.add("dropdown-menu-end");
    for (let i = 0; i < notifications.length; i++) {
        const notification = notifications[i];
        if (!notification.isRead) {
            hasNotifications = true;
            const notificationAlert = document.getElementById("notiNewAlert");
            notificationAlert.classList.add("d-none");
        }
        const notiObject = document.createElement("li");
        notiObject.classList.add("dropdown-item");
        const notiText = getNotificationText(notification.notification);
        const notiLink = getNotificationLink(notification.notification);
        if (!notiText) {
            continue;
        }
        const notiLinkObj = document.createElement("div");
        notiLinkObj.onclick = () => {
            window.location.replace(notiLink);
        };
        notiLinkObj.innerHTML = `
            <div class="d-flex flex-row justify-content-between align-items-center notificationItem" style="min-width: 20rem; min-height: 2.5rem">
                <div class="flex-column" style="width: 10px; height: 10px">
                    <span class="position-absolute p-1 bg-danger border border-light rounded-circle ${
                        notification.isRead ? "d-none" : ""
                    }"></span>
                </div>
                <div class="d-flex flex-column">${notiText}</span>
            </div>
        `;
        notiObject.appendChild(notiLinkObj);
        newList.appendChild(notiObject);
    }
    notificationList.replaceWith(newList);
}

function checkLoggedIn() {
    let isLoggedIn = initUser();
    if (!isLoggedIn) {
        return;
    }
    connectNotifications();
}

function connectNotifications() {
    const token = localStorage.getItem("token");
    const api_url = constants.BACKEND_SOCKET_HOST + constants.BACKEND_NOTIFICATION_API;
    const notificationSocket = new WebSocket(api_url);
    const notificationBtn = document.getElementById("navNotifications");
    notificationBtn.addEventListener("show.bs.dropdown", () => {
        notificationSocket.send(
            JSON.stringify({
                type: "client.read",
                authorization: token,
            })
        );
        const notificationAlert = document.getElementById("notiNewAlert");
        notificationAlert.classList.add("d-none");
    });
    notificationSocket.onopen = () => {
        notificationSocket.send(
            JSON.stringify({
                type: "client.register",
                authorization: token,
            })
        );
        notificationSocket.send(
            JSON.stringify({
                type: "client.notifications",
                authorization: token,
            })
        );
    };
    notificationSocket.onmessage = (e) => {
        if (!e.data) return;
        const data = JSON.parse(e.data);
        if (data.type === "notification_list") {
            const notifications = data.data;
            renderNotifications(notifications);
        } else if (data.type === "notification") {
            addNotification(data);
        }
    };
}

checkLoggedIn();
