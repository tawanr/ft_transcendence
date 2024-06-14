import { fetchHTML, getUserToken } from "../../js/utils.js";
import * as constants from "../../js/constants.js";
import { fetchFriends } from "../../js/user.js";

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
        const form = this.shadow.getElementById("friendAddName");
        const friendName = form.value;
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

    set requests(data) {
        console.log("In set requests")
        console.log("data: ", data)
        this._requests = data;
        this.updateRequests();
    }

    get friends() {
        return this._friends;
    }

    set friends(data) {
        console.log("In set friends")
        this._friends = data;
        this.updateFriends();
    }


    get pending() {
        return this._pending;
    }

    set pending(data) {
        this._pending = data;
    }

    updateRequests() {
        console.log("Updating requests");
        const inviteList = this.shadow.getElementById("inviteList");
        const currentLen = inviteList.querySelectorAll(".friendlistItem").length;
        console.log("currentLen: ", currentLen);
        console.log("this.requests.length: ", this.requests.length);

        // Remove excess items
        if (currentLen > this.requests.length) {
            for (let i = this.requests.length; i < currentLen; i++) {
                inviteList.querySelectorAll(".friendlistItem")[i].remove();
            }
        }

        // First loop: Create or update HTML elements
        for (let i = 0; i < this.requests.length; i++) {
            let friend = this.requests[i];
            let friendItem;

            if (i >= currentLen) {
                // Create new friendItem if it doesn't exist
                friendItem = document.createElement("li");
                friendItem.classList.add("friendlistItem", "list-group-item");
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
                            Pending
                        </div>
                        <div class="d-flex flex-column justify-content-center">
                            <div class="d-flex flex-row">
                                <div class="text-center friendIcon align-middle">
                                    <a href="javascript:void(0)" class="friendAllowBtn"><img src="static/check.svg" /></a>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                if (friend.playerName === localStorage.getItem("username")) {
                    const friendIcon = friendItem.querySelector(".friendIcon");
                    friendIcon.classList.add("d-none");
                }

                inviteList.appendChild(friendItem);
            } else {
                // Update existing friendItem
                friendItem = inviteList.querySelectorAll(".friendlistItem")[i];
            }

            // Update friendItem details (avatar, playerName, status)
            friendItem.querySelector(".avatar").src = friend.avatar;
            friendItem.querySelector(".date").innerText = friend.playerName;
            friendItem.querySelector(".friendStatus").innerText = "Pending";
        }

        // Second loop: Add event listeners using closure
        const allowBtns = inviteList.querySelectorAll(".friendAllowBtn");
        for (let i = 0; i < allowBtns.length; i++) {
            const friend = this.requests[i]; // Capture friend object for this iteration

            (function(friend, self) { // pass 'self' as 'this' context
                allowBtns[i].addEventListener("click", async function() {
                    console.log("allow btn friend.playerName: ", friend.playerName);
                    await self.allowRequest(friend.playerId, friend.playerName);
                });
            })(friend, this); // Pass 'this' as 'self' to the closure
        }

        // Hide friendDelBtn if it's not initialized
        if (!this.friendDelBtn) {
            this.shadow.querySelectorAll("#friendDelBtn").forEach((element) => {
                element.classList.add("d-none");
            });
        }
    }

    updateFriends() {
        console.log("Updating friends");
        const friendList = this.shadow.getElementById("friendList");
        const currentLen = friendList.querySelectorAll(".friendlistItem").length;
        console.log("currentLen: ", currentLen);
        console.log("this.friends.length: ", this.friends.length);

        // Remove excess items
        if (currentLen > this.friends.length) {
            for (let i = this.friends.length; i < currentLen; i++) {
                friendList.querySelectorAll(".friendlistItem")[i].remove();
            }
        }

        // First loop: Create or update HTML elements
        for (let i = 0; i < this.friends.length; i++) {
            let friend = this.friends[i];
            let friendItem;

            if (i >= currentLen) {
                // Create new friendItem if it doesn't exist
                friendItem = document.createElement("li");
                friendItem.classList.add("friendlistItem", "list-group-item");
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
                                    <a href="javascript:void(0)" class="friendChatBtn"><img src="static/chat-fill.svg" /></a>
                                </div>
                                <div class="text-center friendIcon align-middle">
                                    <a href="javascript:void(0)" class="friendDelBtn"><img src="static/x-lg.svg" /></a>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                if (friend.playerName === localStorage.getItem("username")) {
                    const friendIcon = friendItem.querySelector(".friendIcon");
                    friendIcon.classList.add("d-none");
                }

                friendList.appendChild(friendItem);
            } else {
                // Update existing friendItem
                friendItem = friendList.querySelectorAll(".friendlistItem")[i];
            }

            // Update friendItem details (avatar, playerName, status)
            friendItem.querySelector(".avatar").src = friend.avatar;
            friendItem.querySelector(".date").innerText = friend.playerName;
            friendItem.querySelector(".friendStatus").innerHTML = this.getStatusBadge(friend);
        }

        // Second loop: Add event listeners using closure
        const chatBtns = friendList.querySelectorAll(".friendChatBtn");
        const delBtns = friendList.querySelectorAll(".friendDelBtn");

        for (let i = 0; i < chatBtns.length; i++) {
            const friend = this.friends[i]; // Capture friend object for this iteration

            (function(friend, self) { // pass 'self' as 'this' context
                chatBtns[i].addEventListener("click", () => {
                    self.connectChat(friend.playerId, friend.playerName);
                });
                delBtns[i].addEventListener("click", async () => {
                    await self.deleteFriend(friend.playerName);
                });
            })(friend, this); // Pass 'this' as 'self' to the closure
        }

        // Hide friendDelBtn if it's not initialized
        if (!this.friendDelBtn) {
            this.shadow.querySelectorAll("#friendDelBtn").forEach((element) => {
                element.classList.add("d-none");
            });
        }
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
            this.addFriendSubmit();
        });
    }

    async getPlayerStatus(playerName, friendsList) {
        try {
            // Find the player in the provided friends list
            const friend = friendsList.data.find(friend => friend.playerName === playerName);

            // Check if the player is found and return their status
            if (friend) {
                return friend.status;
            } else {
                throw new Error(`Player ${playerName} not found`);
            }
        } catch (error) {
            console.error('Error fetching player status:', error);
            return null;
        }
    }


    async allowRequest(id, name) {
        console.log("In allowRequest")
        console.log("xxxname: ", name)
        const token = getUserToken();
        if (!token) {
            return false;
        }
        const api_url = constants.BACKEND_HOST + "/account/friends/accept/";
        let result = false;
        await fetch(api_url, {
            method: "POST",
            headers: {
                Authorization: "Bearer " + token,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username: name }),
        }).then(async (response) => {
            if (response.status !== 200) {
                console.error("Error accepting friend");
                result = false;
            } else {
                result = true;

                // Find and remove the accepted request from _requests
                const friend = this._requests.find(request => request.playerName === name);
                if (friend) {
                    const updatedRequests = this._requests.filter(friend => friend.playerName !== name);
                    this.requests = updatedRequests;

                    // Fetch the updated friend list
                    const friendList = await fetchFriends();

                    // Get the status of the new friend
                    const playerStatus = await this.getPlayerStatus(name, friendList);

                    // Create the new friend object
                    const newFriend = {
                        playerId: friend.playerId, // retain the original playerId
                        playerName: name,
                        status: playerStatus,
                        avatar: friend.avatar || "default_avatar.png" // use the original avatar or a default one
                    };

                        // Add the new friend to the _friends array and update the DOM
                        this._friends.push(newFriend);
                        this.friends = this._friends; // This will call the set friends() method
                }
            }
        });
        return result;
    }

    async deleteFriend(friendName) {
        console.log("In deleteFriend")
        console.log("friendName: ", friendName)
        const token = getUserToken();
        if (!token) {
            return false;
        }
        const api_url = constants.BACKEND_HOST + "/account/friends/block/";
        let result = false;
        await fetch(api_url, {
            method: "POST",
            headers: {
                Authorization: "Bearer " + token,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username: friendName }),
        }).then(async (response) => {
            if (response.status !== 200) {
                console.error("Error deleting friend");
                result = false;
            } else {
                result = true;
                // Update the friends list instead of reloading the page
                const updatedFriends = this._friends.filter(friend => friend.playerName !== friendName);
                console.log("Updated Friends: ", updatedFriends);
                this.friends = updatedFriends; // This will call the set friends() method
            }
        });
        return result;
    }
}

customElements.define("friend-list", FriendList);

    // updateRequests() {
    //     console.log("Updating requests");
    //     const inviteList = this.shadow.getElementById("inviteList");
    //     const currentLen = inviteList.querySelectorAll(".friendlistItem").length;
    //     console.log("currentLen: ", currentLen)
    //     console.log("this.requests.length: ", this.requests.length)

    //     //Remove excess items
    //     if (currentLen > this.requests.length) {
    //         for (let i = this.requests.length; i < currentLen; i++) {
    //             inviteList.querySelectorAll(".friendlistItem")[i].remove();
    //         }
    //     }

    //     // Add or update items
    //     for (let i = 0; i < this.requests.length; i++) {
    //         console.log("In for loop of add update requests")
    //         let friend = this.requests[i];
    //         let friendItem;
    //         console.log("i: ", i)
    //         console.log("currentLen: ", currentLen)
    //         console.log("friend.playerName: ", friend.playerName);
    //         if (i >= currentLen) {
    //             friendItem = document.createElement("li");
    //             friendItem.classList.add("friendlistItem", "list-group-item");
    //             friendItem.innerHTML = `
    //                 <div class="d-flex flex-row justify-content-around w-100 h-100">
    //                     <div class="d-flex flex-row text-start w-100">
    //                         <div class="d-flex flex-column px-3 justify-content-center">
    //                             <img src="${friend.avatar}" class="avatar" />
    //                         </div>
    //                         <div class="d-flex flex-column justify-content-center">
    //                             <span class="date fs-5">${friend.playerName}</span>
    //                         </div>
    //                     </div>
    //                     <div class="d-flex flex-row align-items-center text-start friendStatus me-3">
    //                         Pending
    //                     </div>
    //                     <div class="d-flex flex-column justify-content-center">
    //                         <div class="d-flex flex-row">
    //                             <div class="text-center friendIcon align-middle">
    //                                 <a href="javascript:void(0)" id="friendAllowBtn"><img src="static/check.svg" /></a>
    //                             </div>
    //                         </div>
    //                     </div>
    //                 </div>
    //             `;
    //             const allowBtn = friendItem.querySelector("#friendAllowBtn");

    //             console.log("Before in event, playerName: ", friend.playerName)
    //             allowBtn.addEventListener("click", async () => {
    //                 console.log("allow btn friend.playerName: ", friend.playerName)
    //                 await this.allowRequest(friend.playerId, friend.playerName);
    //             });

    //             // allowBtn.addEventListener("click", async function(friend) {
    //             //     console.log("allow btn friend.playerName: ", friend.playerName);
    //             //     await this.allowRequest(friend.playerId, friend.playerName);
    //             // }.bind(this, friend));

    //             if (friend.playerName === localStorage.getItem("username")) {
    //                 const friendIcon = friendItem.querySelector(".friendIcon");
    //                 friendIcon.classList.add("d-none");
    //             }
    //             inviteList.appendChild(friendItem);
    //         } else {
    //             friendItem = inviteList.querySelectorAll(".friendlistItem")[i];
    //         }
    //         friendItem.querySelector(".avatar").src = friend.avatar;
    //         friendItem.querySelector(".date").innerText = friend.playerName;
    //         friendItem.querySelector(".friendStatus").innerText = "Pending";
    //     }

    //     if (!this.friendDelBtn) {
    //         this.shadow.querySelectorAll("#friendDelBtn").forEach((element) => {
    //             element.classList.add("d-none");
    //         });
    //     }
    // }


    //     updateFriends() {
    //     console.log("Updating friends");
    //     const friendList = this.shadow.getElementById("friendList");
    //     const currentLen = friendList.querySelectorAll(".friendlistItem").length;
    //     console.log("currentLen: ", currentLen)
    //     console.log("this.friends.length: ", this.friends.length)

    //     // Remove excess items
    //     if (currentLen > this.friends.length) {
    //         for (let i = this.friends.length; i < currentLen; i++) {
    //             friendList.querySelectorAll(".friendlistItem")[i].remove();
    //         }
    //     }

    //     // Add or update items
    //     for (let i = 0; i < this.friends.length; i++) {
    //         let friend = this.friends[i];
    //         console.log(friend)
    //         let friendItem;
    //         if (i >= currentLen) {
    //             friendItem = document.createElement("li");
    //             friendItem.classList.add("friendlistItem", "list-group-item");
    //             friendItem.innerHTML = `
    //                 <div class="d-flex flex-row justify-content-around w-100 h-100">
    //                     <div class="d-flex flex-row text-start w-100">
    //                         <div class="d-flex flex-column px-3 justify-content-center">
    //                             <img src="${friend.avatar}" class="avatar" />
    //                         </div>
    //                         <div class="d-flex flex-column justify-content-center">
    //                             <span class="date fs-5">${friend.playerName}</span>
    //                         </div>
    //                     </div>
    //                     <div class="d-flex flex-row align-items-center text-start friendStatus me-3">
    //                         ${this.getStatusBadge(friend)}
    //                     </div>
    //                     <div class="d-flex flex-column justify-content-center">
    //                         <div class="d-flex flex-row">
    //                             <div class="text-center friendIcon align-middle">
    //                                 <a href="javascript:void(0)" id="friendChatBtn"><img src="static/chat-fill.svg" /></a>
    //                             </div>
    //                             <div id="friendDelBtn" class="text-center friendIcon align-middle">
    //                                 <a href="javascript:void(0)"><img src="static/x-lg.svg" /></a>
    //                             </div>
    //                         </div>
    //                     </div>
    //                 </div>
    //             `;
    //             const chatBtn = friendItem.querySelector("#friendChatBtn");
    //             chatBtn.addEventListener("click", () => {
    //                 this.connectChat(friend.playerId, friend.playerName);
    //             });
    //             const delBtn = friendItem.querySelector("#friendDelBtn");
    //             console.log("Before event, friend.playerName: ", friend.playerName)
    //             delBtn.addEventListener("click", async () => {
    //                 console.log("del button friend.playerName: ", friend.playerName)
    //                 await this.deleteFriend(friend.playerName);
    //             });
    //             if (friend.playerName === localStorage.getItem("username")) {
    //                 const friendIcon = friendItem.querySelector(".friendIcon");
    //                 friendIcon.classList.add("d-none");
    //             }
    //             friendList.appendChild(friendItem);
    //         } else {
    //             friendItem = friendList.querySelectorAll(".friendlistItem")[i];
    //         }
    //         friendItem.querySelector(".avatar").src = friend.avatar;
    //         friendItem.querySelector(".date").innerText = friend.playerName;
    //         friendItem.querySelector(".friendStatus").innerHTML = this.getStatusBadge(friend);
    //     }

    //     if (!this.friendStatusBadge) {
    //         this.shadow.querySelectorAll(".friendStatus").forEach((element) => {
    //             element.classList.add("d-none");
    //         });
    //     }
    //     if (!this.friendDelBtn) {
    //         this.shadow.querySelectorAll("#friendDelBtn").forEach((element) => {
    //             element.classList.add("d-none");
    //         });
    //     }
    // }
