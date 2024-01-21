import { fetchHTML } from "../../js/utils.js";
import "../bracket-game/bracket-game.js";

class Bracket extends HTMLElement {
    constructor() {
        super();
        this.friendAddBtn = false;
        this.shadow = this.attachShadow({ mode: "closed" });
        fetchHTML("/components/bracket/bracket.html").then((html) => {
            this.render(html);
        });
        this.cardTitle = this.getAttribute("title");
    }

    connectedCallback() {
        this.tournamentSize = 8;
        this.bracket = [
            {
                finished: true,
                players: [
                    {
                        id: 1,
                        name: "AAA",
                        score: 0,
                        isWinner: false,
                    },
                    {
                        id: 2,
                        name: "BBB",
                        score: 5,
                        isWinner: true,
                    },
                ],
            },
            {
                finished: true,
                players: [
                    {
                        id: 3,
                        name: "CCC",
                        score: 5,
                        isWinner: true,
                    },
                    {
                        id: 4,
                        name: "DDD",
                        score: 3,
                        isWinner: false,
                    },
                ],
            },
            {
                finished: true,
                players: [
                    {
                        id: 1,
                        name: "AAA",
                        score: 0,
                        isWinner: false,
                    },
                    {
                        id: 2,
                        name: "BBB",
                        score: 5,
                        isWinner: true,
                    },
                ],
            },
            {
                finished: true,
                players: [
                    {
                        id: 3,
                        name: "CCC",
                        score: 5,
                        isWinner: true,
                    },
                    {
                        id: 4,
                        name: "DDD",
                        score: 3,
                        isWinner: false,
                    },
                ],
            },
            {
                finished: false,
                players: [
                    {
                        id: 2,
                        name: "BBB",
                        score: 0,
                        isWinner: false,
                    },
                    {
                        id: 3,
                        name: "CCC",
                        score: 0,
                        isWinner: false,
                    },
                ],
            },
            {},
            {},
        ];
    }

    render(html) {
        this.shadow.innerHTML = html;

        const bracket = this.shadow.getElementById("tourBracket");

        let currentRoundLimit = this.tournamentSize / 2 || this.bracket.length * 2;
        let bracketColumn = document.createElement("div");
        bracketColumn.classList.add("bracketColumn");

        for (let i = 0; i < this.tournamentSize - 1; i++) {
            if (i === currentRoundLimit) {
                currentRoundLimit += currentRoundLimit / 2;
                bracket.appendChild(bracketColumn);
                bracketColumn = document.createElement("div");
                bracketColumn.classList.add("bracketColumn");
            }
            const bracketGame = document.createElement("bracket-game");
            bracketGame.classList.add("bracketGame");
            bracketGame.players = this.bracket[i].players;
            bracketColumn.appendChild(bracketGame);
        }

        bracket.appendChild(bracketColumn);
    }
}

customElements.define("bracket-component", Bracket);
