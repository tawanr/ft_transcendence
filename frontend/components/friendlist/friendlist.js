import { fetchHTML } from "../../js/utils.js";

class FriendList extends HTMLElement {
    constructor() {
        super();
        this.shadow = this.attachShadow({ mode: "closed" });
        fetchHTML("/components/friendlist/friendlist.html").then((html) => {
            this.render(html);
        });
    }

    connectedCallback() {
        this.friends = [
            {
                playerName: "AAA",
                playerId: 123,
                avatar: "/uploads/avatars/42_Logo.png",
                status: "offline",
            },
            {
                playerName: "def",
                playerId: 123,
                avatar: "/uploads/avatars/42_Logo.png",
                status: "online",
            },
            {
                playerName: "zzz",
                playerId: 123,
                avatar: "/uploads/avatars/42_Logo.png",
                status: "ingame",
            },
        ];
    }

    getStatusBadge(player) {
        if (player.status === "online") {
            return `<span class="badge bg-success">ONLINE</span>`;
        } else if (player.status === "offline") {
            return `<span class="badge bg-danger">OFFLINE</span>`;
        } else if (player.status === "ingame") {
            return `<span class="badge bg-primary">IN-GAME</span>`;
        }
    }

    render(html) {
        this.shadow.innerHTML = html;

        const friendList = this.shadow.getElementById("friendList");
        for (let i = 0; i < 8; i++) {
            const friend = this.friends[i % 3];
            const friendItem = document.createElement("li");
            friendItem.classList.add("friendlistItem");
            friendItem.classList.add("list-group-item");

            friendItem.innerHTML = `
            <div class="d-flex flex-row justify-content-around w-100 h-100">
                <div class="d-flex flex-row text-start w-100">
                    <div class="d-flex flex-column px-3 justify-content-center">
                        <img src="${friend.avatar}" class="avatar" />
                    </div>
                    <div class="d-flex flex-column justify-content-center">
                        <span class="date fs-5">${friend.playerName}</span>
                    </div>
                </div>
                <div class="d-flex flex-row align-items-center friendStatus me-3">
                    ${this.getStatusBadge(friend)}
                </div>
                <div class="d-flex flex-column justify-content-center">
                    <div class="d-flex flex-row">
                        <div class="text-center friendIcon align-middle">
                            <a href="#"><img src="static/chat-fill.svg" /></a>
                        </div>
                        <div class="text-center friendIcon align-middle">
                            <a href="#"><img src="static/x-lg.svg" /></a>
                        </div>
                    </div>
                </div>
            </div>
            `;
            console.log(friendItem);

            friendList.appendChild(friendItem);
        }
    }
}

customElements.define("friend-list", FriendList);
