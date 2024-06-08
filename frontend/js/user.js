import { getUserToken } from "./utils.js";
import * as constants from "./constants.js";
import { GameHistory } from "./models/game-history.js";

/**
 * Get the game history for the current user
 *
 * @returns {GameHistory[]}
 */
export async function fetchUserHistory() {
    const token = getUserToken();
    if (!token) {
        return null;
    }
    const api_url = constants.BACKEND_HOST + "/account/history/";
    let histories = [];
    await fetch(api_url, {
        method: "GET",
        headers: {
            Authorization: "Bearer " + token,
        },
    }).then(async (response) => {
        if (response.status !== 200) {
            console.error("Error fetching user history");
            return [];
        }
        await response.json().then((data) => {
            let games = data["data"];
            for (let i = 0; i < games.length; i++) {
                histories.push(Object.assign(new GameHistory(), games[i]));
            }
        });
    });
    return histories;
}

export async function fetchFriends() {
    const token = getUserToken();
    if (!token) {
        return null;
    }
    const api_url = constants.BACKEND_HOST + "/account/friends/";
    // let friends = [];
    let friends = {};
    await fetch(api_url, {
        method: "GET",
        headers: {
            Authorization: "Bearer " + token,
        },
    }).then(async (response) => {
        if (response.status !== 200) {
            console.error("Error fetching friends");
            return [];
        }
        await response.json().then((data) => {
            // friends = data["data"];
            friends["data"] = data["data"];
            friends["pending"] = data["pending"];
            friends["requests"] = data["requests"]
        });
    });
    return friends;
}

export async function addFriend(friendName) {
    const token = getUserToken();
    if (!token) {
        return false;
    }
    const api_url = constants.BACKEND_HOST + "/account/friends/";
    let result = false;
    await fetch(api_url, {
        method: "POST",
        headers: {
            Authorization: "Bearer " + token,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: friendName }),
    }).then(async (response) => {
        if (response.status !== 200) {
            console.error("Error adding friend");
            result = false;
        } else {
            result = true;
        }
    });
    return result;
}
