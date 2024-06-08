import { fetchFriends, addFriend } from "./user.js";

const friendlist = document.querySelector("friend-list");

async function addFriendCallback(username) {
    const result = await addFriend(username);
    if (result) {
        const friends = await fetchFriends();
        friendlist.friends = friends;
    }
    return result;
}

async function setup() {
    const friends = await fetchFriends();
    friendlist.friends = friends;
    friendlist.setCallback(addFriendCallback);
}

setup();
