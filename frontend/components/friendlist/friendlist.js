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
                playerName: "abc",
                playerId: 123,
                avatar: "/uploads/avatars/42_Logo.png",
            },
        ];
    }

    render(html) {
        this.shadow.innerHTML = html;

        const friendList = this.shadow.getElementById("friendList");
        for (let i = 0; i < 10; i++) {
            const friend = this.friends[0];
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
                        <span class="date fs-4 fw-bold">${friend.playerName}</span>
                    </div>
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
