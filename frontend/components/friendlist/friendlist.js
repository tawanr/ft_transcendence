import { fetchHTML } from "../../js/utils.js";

class FriendList extends HTMLElement {
    constructor() {
        super();
        this.friendAddBtn = false;
        this.shadow = this.attachShadow({ mode: "closed" });
        fetchHTML("/components/friendlist/friendlist.html").then((html) => {
            this.html = html;
            this.render(html);
        });
        this.cardTitle = this.getAttribute("title");
    }

    get friends() {
        return this._friends;
    }

    set friends(data) {
        this._friends = data;
        const friendList = this.shadow.getElementById("friendList");
        const currentLen = friendList.querySelectorAll(".friendlistItem").length;
        if (currentLen > this.friends.length) {
            for (let i = this.friends.length; i < currentLen; i++) {
                friendList.querySelectorAll(".friendlistItem")[i].remove();
            }
        }
        for (let i = 0; i < this.friends.length; i++) {
            const friend = this.friends[i];
            let friendItem;
            if (i >= friendList.querySelectorAll(".friendlistItem").length) {
                friendItem = document.createElement("li");
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
                    <div class="d-flex flex-row align-items-center text-start friendStatus me-3">
                        ${this.getStatusBadge(friend)}
                    </div>
                    <div class="d-flex flex-column justify-content-center">
                        <div class="d-flex flex-row">
                            <div class="text-center friendIcon align-middle">
                                <a href="#"><img src="static/chat-fill.svg" /></a>
                            </div>
                            <div id="friendDelBtn" class="text-center friendIcon align-middle">
                                <a href="#"><img src="static/x-lg.svg" /></a>
                            </div>
                        </div>
                    </div>
                </div>
                `;
                friendList.appendChild(friendItem);
            } else {
                friendItem = friendList.querySelectorAll(".friendlistItem")[i];
            }
            friendItem.querySelector(".avatar").src = friend.avatar;
            friendItem.querySelector(".date").innerText = friend.playerName;
            friendItem.querySelector(".friendStatus").innerHTML =
                this.getStatusBadge(friend);
        }

        if (!this.friendStatusBadge) {
            this.shadow.querySelectorAll(".friendStatus").forEach((element) => {
                element.classList.add("d-none");
            });
        }
        if (!this.friendDelBtn) {
            this.shadow.querySelectorAll("#friendDelBtn").forEach((element) => {
                element.classList.add("d-none");
            });
        }
    }

    connectedCallback() {
        this._friends = [];
        this.friendDelBtn = this.hasAttribute("friend-del-btn");
        this.friendStatusBadge = this.hasAttribute("show-status");
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
        if (this.cardTitle) {
            const cardTitle = this.shadow.getElementById("cardTitle");
            cardTitle.innerText = this.cardTitle;
        }
    }
}

customElements.define("friend-list", FriendList);
