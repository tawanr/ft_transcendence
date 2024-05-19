import { fetchHTML } from "../../js/utils.js";
import { GameHistory } from "../../js/models/game-history.js";
import { fetchUserHistory } from "../../js/user.js";

class UserHistory extends HTMLElement {
    constructor() {
        super();
        this.shadow = this.attachShadow({ mode: "closed" });
        fetchHTML("/components/user-history/user-history.html").then((html) => {
            this._html = html;
            this.render();
        });
        this.getUserHistory();
    }

    async getUserHistory() {
        await fetchUserHistory().then((data) => {
            this.histories = data;
        });
    }

    set histories(data) {
        if (!data) {
            return;
        }
        this._histories = data;
        this.render(this.html);
    }

    /**
     * History data for the current user
     *
     * @readonly
     * @type {GameHistory[]}
     */
    get histories() {
        return this._histories;
    }

    connectedCallback() {
        this.maxList = 25;
        if (this.hasAttribute("max-list")) {
            this.maxList = parseInt(this.getAttribute("max-list"));
        }
        this.histories = [];
    }

    render() {
        this.shadow.innerHTML = this._html;

        const historyList = this.shadow.getElementById("historyList");
        for (let i = 0; i < this.maxList && i < this.histories.length; i++) {
            const historyItem = document.createElement("li");
            const history = this.histories[i];
            historyItem.classList.add("historyItem");
            historyItem.classList.add("list-group-item");
            const victory = this.histories[i].isWinner
                ? "<span class='text-success'>Victory</span>"
                : "<span class='text-danger'>Defeat</span>";
            historyItem.innerHTML = `
            <div class="d-flex flex-row justify-content-around w-100 h-100 align-items-center px-3">
                <div class="d-flex flex-column text-start w-100">
                    <div class="d-flex flex-row align-items-center">
                        <div class="flex-column px-3">
                            <img src="${history.player1Avatar}" class="avatar" />
                        </div>
                        <div class="d-flex flex-column">
                            <span class="date fs-4 fw-bold">${history.player1Name}</span>
                        </div>
                    </div>
                </div>
                <div class="d-flex flex-column flex-grow-1 w-100">
                    <div class="flex-row justify-content-center text-center">
                        <span class="fs-2 fw-bold">${history.score}</span>
                    </div>
                    <div class="flex-row justify-content-center text-center fw-bold">
                        ${victory}
                    </div>
                </div>
                <div class="flex-column text-end w-100">
                    <div class="d-flex flex-row w-100 justify-content-end align-items-center">
                        <div class="d-flex flex-column">
                            <span class="date fs-4 fw-bold">${history.player2Name}</span>
                        </div>
                        <div class="flex-column px-3">
                            <img src="${history.player2Avatar}" class="avatar" />
                        </div>
                    </div>
                </div>
            </div>
            `;
            historyList.appendChild(historyItem);
        }
    }
}

customElements.define("user-history", UserHistory);
