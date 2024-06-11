import { fetchFriends, addFriend } from "./user.js";

const friendlist = document.querySelector("friend-list");

async function addFriendCallback(username) {
    const result = await addFriend(username);
    if (result) {
        const friends_data = await fetchFriends();
        friendlist.friends = friends_data["data"];
        friendlist.pending = friends_data["pending"];
        friendlist.requests = friends_data["requests"];

        // const friends = await fetchFriends();
        // friendlist.friends = friends;
    }
    return result;
}

async function setup() {
    const friends_data = await fetchFriends();
    friendlist.friends = friends_data["data"];
    friendlist.pending = friends_data["pending"];
    friendlist.requests = friends_data["requests"];

    // const friends = await fetchFriends();
    // friendlist.friends = friends;
    friendlist.setCallback(addFriendCallback);
}

setup();
