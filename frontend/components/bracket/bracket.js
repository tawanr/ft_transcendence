import { fetchHTML } from "../../js/utils.js";
import "../bracket-game/bracket-game.js";

/**
 * @typedef {Object} BracketPlayer
 * @property {number} id
 * @property {string} name
 * @property {number} score
 * @property {boolean} isWinner
 */

/**
 * @typedef {Object} BracketGame
 * @property {boolean} finished
 * @property {BracketPlayer[]} players
 */

class Bracket extends HTMLElement {
    /**
     * Creates an instance of Bracket.
     *
     * @constructor
     */
    constructor() {
        super();
        this.friendAddBtn = false;
        this.shadow = this.attachShadow({ mode: "closed" });
        fetchHTML("/components/bracket/bracket.html").then((html) => {
            this.html = html;
            this.render(html);
        });
        this.cardTitle = this.getAttribute("title");
    }

    set bracket(data) {
        this._bracket = data.bracket;
        this.tournamentSize = data.size;
        this.render(this.html);
    }

    /**
     * Bracket data
     *
     * @type {BracketGame[]}
     */
    get bracket() {
        return this._bracket;
    }

    connectedCallback() {
        /** @type {number} */
        this.tournamentSize = 0;
        /** @type {BracketGame[]} */
        this._bracket = [];
    }

    /**
     * Render component
     *
     * @param {*} html
     */
    render(html) {
        this.shadow.innerHTML = html;

        /** @type {HTMLElement} */
        const bracket = this.shadow.getElementById("tourBracket");

        let currentRoundLimit = this.tournamentSize / 2 || this.bracket.length * 2;
        let currentRoundCount = this.tournamentSize / 2 || this.bracket.length * 2;
        let bracketColumn = document.createElement("div");
        bracketColumn.classList.add("bracketColumn");

        for (let i = 0; i < this.tournamentSize - 1; i++) {
            if (i === currentRoundLimit) {
                currentRoundCount /= 2;
                currentRoundLimit += currentRoundCount;
                bracket.appendChild(bracketColumn);
                bracketColumn = document.createElement("div");
                bracketColumn.classList.add("bracketColumn");

                const padderLeft = document.createElement("div");
                padderLeft.classList.add("bracketLinkLeft");
                padderLeft.style.height = `${100 / (currentRoundCount * 2)}%`;
                const paddingColumnLeft = document.createElement("div");
                paddingColumnLeft.classList.add("bracketColumn");
                for (let j = 0; j < currentRoundCount; j++) {
                    paddingColumnLeft.appendChild(padderLeft.cloneNode(true));
                }

                const padderRight = document.createElement("div");
                padderRight.classList.add("bracketLinkRight");
                padderLeft.style.height = `${100 / currentRoundCount}%`;
                const paddingColumnRight = document.createElement("div");
                paddingColumnRight.classList.add("bracketColumn");
                for (let j = 0; j < currentRoundCount; j++) {
                    paddingColumnRight.appendChild(padderRight.cloneNode(true));
                }

                bracket.appendChild(paddingColumnLeft);
                bracket.appendChild(paddingColumnRight);
            }
            const bracketGame = document.createElement("bracket-game");
            bracketGame.classList.add("bracketGame");
            let players = [];
            if (i < this.bracket.length) {
                players = this.bracket[i].players;
            }
            bracketGame.players = players;
            bracketColumn.appendChild(bracketGame);
        }

        bracket.appendChild(bracketColumn);
    }
}

customElements.define("bracket-component", Bracket);
