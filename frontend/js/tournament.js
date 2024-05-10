import * as constants from "./constants.js";
import { getUserToken } from "./utils.js";

const pointerScroll = (elem) => {
    let isDrag = false;

    const dragStart = () => (isDrag = true);
    const dragEnd = () => (isDrag = false);
    const drag = (ev) =>
        isDrag && (elem.scrollLeft -= ev.movementX) && (elem.scrollTop -= ev.movementY);

    elem.addEventListener("pointerdown", dragStart);
    addEventListener("pointerup", dragEnd);
    addEventListener("pointermove", drag);
};

document.querySelectorAll(".bracketContent").forEach(pointerScroll);

const bracketComp = document.querySelector("bracket-component");
const playerList = document.querySelector("friend-list");

async function getTournamentDetails() {
    const token = getUserToken();
    if (!token) {
        window.location.replace("/login");
        return;
    }
    const api_url = constants.BACKEND_HOST + constants.BACKEND_TOURNAMENT_API;
    await fetch(api_url, {
        method: "GET",
        headers: {
            Authorization: "Bearer " + token,
        },
    }).then((response) => {
        if (response.status !== 200) {
            document.getElementById("activeTour").classList.add("d-none");
            document.getElementById("actionTour").classList.remove("d-none");
            return;
        }
        response.json().then((data) => {
            const bracketHeader = document.getElementById("bracketHeader");
            bracketHeader.innerText = "Tournament Bracket - ID " + data.id;
            bracketComp.bracket = data;
            playerList.friends = data.players;
        });
        document.getElementById("activeTour").classList.remove("d-none");
        document.getElementById("actionTour").classList.add("d-none");
    });
}

function createTournament() {
    const token = getUserToken();
    if (!token) {
        window.location.replace("/login");
        return;
    }
    const api_url = constants.BACKEND_HOST + constants.BACKEND_TOURNAMENT_API;
    fetch(api_url, {
        method: "POST",
        headers: {
            Authorization: "Bearer " + token,
        },
        body: JSON.stringify({
            game_type: "pong",
        }),
    }).then((response) => {
        if (response.status !== 201) {
            // Error Handling
            return;
        }
        getTournamentDetails();
    });
}

function joinTournament() {
    const token = getUserToken();
    if (!token) {
        window.location.replace("/login");
        return;
    }
    const tournamentId = document.getElementById("tournamentId").value;
    const api_url =
        constants.BACKEND_HOST +
        constants.BACKEND_TOURNAMENT_API +
        tournamentId +
        "/join/";
    fetch(api_url, {
        method: "POST",
        headers: {
            Authorization: "Bearer " + token,
        },
    }).then((response) => {
        if (response.status !== 200) {
            // Error Handling
            return;
        }
        getTournamentDetails();
    });
}

function setup() {
    document
        .getElementById("createTournamentBtn")
        .addEventListener("click", createTournament);
    document
        .getElementById("joinTournamentBtn")
        .addEventListener("click", joinTournament);
    getTournamentDetails();
}

setup();
