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

    addFriendToggle() {
        const addFriendDialog = this.shadow.querySelector(".addFriendDialog");
        addFriendDialog.classList.toggle("d-none");
    }

    async addBtnFn(friendName) {
        if (this.addCallback) {
            return await this.addCallback(friendName);
        }
    }

    async addFriendSubmit() {
        console.log("Hello")
        const form = this.shadow.getElementById("friendAddName");
        const friendName = form.value;
        console.log(friendName);
        if (!friendName) {
            return;
        }
        const result = await this.addBtnFn(friendName);
        if (!result) {
            form.classList.add("is-invalid");
        } else {
            form.classList.remove("is-invalid");
            form.value = "";
        }
    }

    setCallback(callback) {
        this.addCallback = callback;
    }

    get invites() {
        return this._invites;
    }

    set invites(data) {
        this._invites = data;
    }

    get requests() {
        return this._requests;
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
                                <a href="javascript:void(0)" id="friendChatBtn"><img src="static/chat-fill.svg" /></a>
                            </div>
                            <div id="friendDelBtn" class="text-center friendIcon align-middle">
                                <a href="#"><img src="static/x-lg.svg" /></a>
                            </div>
                        </div>
                    </div>
                </div>
                `;
                const chatBtn = friendItem.querySelector("#friendChatBtn");
                chatBtn.addEventListener("click", () => {
                    this.connectChat(friend.playerId, friend.playerName);
                });
                if (friend.playerName === localStorage.getItem("username")) {
                    const friendIcon = friendItem.querySelector(".friendIcon");
                    friendIcon.classList.add("d-none");
                }
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

    set requests(data) {
        this._requests = data;
        const friendList = this.shadow.getElementById("friendList");
        const currentLen = friendList.querySelectorAll(".friendlistItem").length;
        // if (currentLen > this.requests.length) {
        //     for (let i = this.requests.length; i < currentLen; i++) {
        //         friendList.querySelectorAll(".friendlistItem")[i].remove();
        //     }
        // }
        for (let i = currentLen; i < this.requests.length; i++) {
            const friend = this.requests[i];
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

                    </div>
                    <div class="d-flex flex-column justify-content-center">
                        <div class="d-flex flex-row">
                            <div class="text-center friendIcon align-middle">
                                <a href="javascript:void(0)" id="friendAllowBtn"><img src="static/chat-fill.svg" /></a>
                            </div>
                            <div id="friendDelBtn" class="text-center friendIcon align-middle">
                                <a href="#"><img src="static/x-lg.svg" /></a>
                            </div>
                        </div>
                    </div>
                </div>
                `;
                const chatBtn = friendItem.querySelector("#friendAllowBtn");
                chatBtn.addEventListener("click", () => {
                    this.connectChat(friend.playerId, friend.playerName);
                });
                if (friend.playerName === localStorage.getItem("username")) {
                    const friendIcon = friendItem.querySelector(".friendIcon");
                    friendIcon.classList.add("d-none");
                }
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

    get pending() {
        return this._pending;
    }

    set pending(data) {
        this._pending = data;
        // const friendList = this.shadow.getElementById("friendList");
        // const currentLen = friendList.querySelectorAll(".friendlistItem").length;
        // if (currentLen > this._pending.length) {
        //     for (let i = this._pending.length; i < currentLen; i++) {
        //         friendList.querySelectorAll(".friendlistItem")[i].remove();
        //     }
        // }
        // for (let i = 0; i < this._pending.length; i++) {
        //     const friend = this._pending[i];
        //     let friendItem;
        //     if (i >= friendList.querySelectorAll(".friendlistItem").length) {
        //         friendItem = document.createElement("li");
        //         friendItem.classList.add("friendlistItem");
        //         friendItem.classList.add("list-group-item");
        //         friendItem.innerHTML = `
        //         <div class="d-flex flex-row justify-content-around w-100 h-100">
        //             <div class="d-flex flex-row text-start w-100">
        //                 <div class="d-flex flex-column px-3 justify-content-center">
        //                     <img src="${friend.avatar}" class="avatar" />
        //                 </div>
        //                 <div class="d-flex flex-column justify-content-center">
        //                     <span class="date fs-5">${friend.playerName}</span>
        //                 </div>
        //             </div>
        //             <div class="d-flex flex-row align-items-center text-start friendStatus me-3">
        //                 ${this.getStatusBadge(friend)}
        //             </div>
        //             <div class="d-flex flex-column justify-content-center">
        //                 <div class="d-flex flex-row">
        //                     <div class="text-center friendIcon align-middle">
        //                         <a href="javascript:void(0)" id="friendAllowBtn"><img src="static/chat-fill.svg" /></a>
        //                     </div>
        //                     <div id="friendDelBtn" class="text-center friendIcon align-middle">
        //                         <a href="#"><img src="static/x-lg.svg" /></a>
        //                     </div>
        //                 </div>
        //             </div>
        //         </div>
        //         `;
        //         const chatBtn = friendItem.querySelector("#friendAllowBtn");
        //         chatBtn.addEventListener("click", () => {
        //             this.connectChat(friend.playerId, friend.playerName);
        //         });
        //         if (friend.playerName === localStorage.getItem("username")) {
        //             const friendIcon = friendItem.querySelector(".friendIcon");
        //             friendIcon.classList.add("d-none");
        //         }
        //         friendList.appendChild(friendItem);
        //     } else {
        //         friendItem = friendList.querySelectorAll(".friendlistItem")[i];
        //     }
        //     friendItem.querySelector(".avatar").src = friend.avatar;
        //     friendItem.querySelector(".date").innerText = friend.playerName;
        //     friendItem.querySelector(".friendStatus").innerHTML =
        //         this.getStatusBadge(friend);
        // }

        // if (!this.friendStatusBadge) {
        //     this.shadow.querySelectorAll(".friendStatus").forEach((element) => {
        //         element.classList.add("d-none");
        //     });
        // }
        // if (!this.friendDelBtn) {
        //     this.shadow.querySelectorAll("#friendDelBtn").forEach((element) => {
        //         element.classList.add("d-none");
        //     });
        // }
    }

    connectChat(id, name) {
        const friendChat = this.shadow.querySelector(".friendChat");
        const chatRoom = friendChat.querySelector("chat-room");
        chatRoom.setAttribute("title", name);
        chatRoom.connectChatRoom("private", id);
        friendChat.classList.remove("d-none");
    }

    connectedCallback() {
        this._friends = [];
        this.friendDelBtn = this.hasAttribute("friend-del-btn");
        this.friendStatusBadge = this.hasAttribute("show-status");
        this.friendAddBtn = this.hasAttribute("friend-add-btn");
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
        console.log("In render()")
        this.shadow.innerHTML = html;
        if (this.cardTitle) {
            const cardTitle = this.shadow.getElementById("cardTitle");
            cardTitle.innerText = this.cardTitle;
        }
        const addFriendBtn = this.shadow.getElementById("friendAddBtn");
        addFriendBtn.addEventListener("click", () => {
            this.addFriendToggle();
        });
        const friendAddSubmit = this.shadow.getElementById("friendAddSubmit");
        friendAddSubmit.addEventListener("click", () => {
            console.log("Before in addFriendSubmit()")
            this.addFriendSubmit();
        });
    }
}

customElements.define("friend-list", FriendList);
