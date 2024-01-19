import { fetchHTML } from "../../js/utils.js";

class GameHistory {
    /**
     * Object for a game history.
     * @param {string} player1Name
     * @param {string} player1Avatar
     * @param {string} player2Name
     * @param {string} player2Avatar
     * @param {boolean} isFinished
     * @param {string} score
     * @param {boolean} isWinner
     * @param {string} date
     */
    constructor(
        player1Name,
        player1Avatar,
        player2Name,
        player2Avatar,
        isFinished,
        score,
        isWinner,
        date
    ) {
        this.player1Name = player1Name;
        this.player1Avatar = player1Avatar;
        this.player2Name = player2Name;
        this.player2Avatar = player2Avatar;
        this.isFinished = isFinished;
        this.score = score;
        this.isWinner = isWinner;
        this.date = date;
    }
}

class UserHistory extends HTMLElement {
    static observedAttributes = [];

    constructor() {
        super();
        this.shadow = this.attachShadow({ mode: "closed" });
        fetchHTML("/components/user-history/user-history.html").then((html) => {
            this.render(html);
        });
    }

    connectedCallback() {
        this.maxList = 25;
        if (this.hasAttribute("max-list")) {
            this.maxList = parseInt(this.getAttribute("max-list"));
        }
        this.histories = [
            new GameHistory(
                "abc",
                "/uploads/avatars/42_Logo.png",
                "def",
                "/uploads/avatars/42_Logo.png",
                true,
                "5 - 0",
                true,
                "2021-05-06"
            ),
            new GameHistory(
                "ggg",
                "/uploads/avatars/42_Logo.png",
                "abc",
                "/uploads/avatars/42_Logo.png",
                true,
                "2 - 5",
                false,
                "2021-05-06"
            ),
        ];
    }

    attributeChangedCallback(name, oldValue, newValue) {}

    render(html) {
        this.shadow.innerHTML = html;

        const historyList = this.shadow.getElementById("historyList");
        for (let i = 0; i < this.maxList; i++) {
            const historyItem = document.createElement("li");
            const history = this.histories[i % 2];
            historyItem.classList.add("historyItem");
            historyItem.classList.add("list-group-item");
            const victory = this.histories[i % 2].isWinner
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
