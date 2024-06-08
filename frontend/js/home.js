import { fetchFriends, addFriend } from "./user.js";

const friendlist = document.querySelector("friend-list");

async function addFriendCallback(username) {
    const result = await addFriend(username);
    if (result) {
        const friends = fetchFriends();
        friendlist.friends = friends;
    }
    return result;
}

function setup() {
    const friends = fetchFriends();
    friendlist.friends = friends;
    friendlist.setCallback(addFriendCallback);
}

setup();
