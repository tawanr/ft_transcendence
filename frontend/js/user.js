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
