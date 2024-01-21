import { fetchHTML } from "../../js/utils.js";

class BracketGame extends HTMLElement {
    constructor() {
        super();
        this.shadow = this.attachShadow({ mode: "closed" });
        this.players = [];
        fetchHTML("/components/bracket-game/bracket-game.html").then((html) => {
            this.html = html;
            this.render();
        });
    }

    connectedCallback() {}

    render() {
        const html = this.html;
        this.shadow.innerHTML = html;
        const playerCards = this.shadow.querySelectorAll(".playerCard");

        if (!this.players) {
            return;
        }
        for (let i = 0; i < 2; i++) {
            const player = this.players[i];
            const playerCard = playerCards[i];
            if (player.name) {
                playerCard.querySelector(".playerName").innerText = player.name;
                playerCard.querySelector(".playerScore").innerText =
                    player.score || "0";
            }
            if (player.isWinner) {
                playerCard.classList.add("playerWinner");
            }
        }
    }
}

customElements.define("bracket-game", BracketGame);
