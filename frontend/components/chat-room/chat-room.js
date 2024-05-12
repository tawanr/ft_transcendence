import { fetchHTML } from "../../js/utils.js";
import { create_chat_socket, websocket_event, send_message } from "./utils_chat_room.js";

class ChatRoom extends HTMLElement {
    constructor() {
        super();
        this.shadow = this.attachShadow({ mode: "closed" });
        fetchHTML("/components/chat-room/chat-room.html").then((html) => {
            this.html = html;
            // this.render();
        });

        this.chats = []

        this.chatSocket = create_chat_socket();
        websocket_event(this);

        this.groupChat = this.hasAttribute("group-chat");
    }

    connectedCallback() {}

    render() {
        this.shadow.innerHTML = this.html;

        const chatList = this.shadow.getElementById("chatList");
        let currentDate = null;
        let currentSender = "";

        for (let i = 0; i < this.chats.length; i++) {
            const chat = this.chats[i];
            if (chat.isSent) {
                currentSender = "";
            }

            if (chat.date !== currentDate) {
                currentDate = chat.date;
                currentSender = "";
                const dateItem = document.createElement("div");
                dateItem.classList.add("chatDate");
                dateItem.innerHTML = new Date(chat.date).toISOString().substring(0, 10);
                chatList.appendChild(dateItem);
            }

            if (this.groupChat && !chat.isSent && chat.senderName !== currentSender) {
                currentSender = chat.senderName;
                const senderItem = document.createElement("div");
                senderItem.classList.add("chatSender");
                senderItem.innerHTML = currentSender;
                chatList.appendChild(senderItem);
            }

            const chatItem = this.renderMessage(chat);
            chatList.appendChild(chatItem);
        }

        this.shadow.getElementById("chatForm").addEventListener("submit", (e) => {
            e.preventDefault();
            this.sendMessage();
        });
    }

    renderMessage(chat) {
        const chatItem = document.createElement("div");
        chatItem.classList.add("chatItem");
        chatItem.classList.add("d-flex");
        chatItem.classList.add(chat.isSent ? "chatSent" : "chatReceived");
        chatItem.innerHTML = `
        <div class="rounded-pill chatBubble">
            ${chat.message}
        </div>
        `;
        return chatItem;
    }

    receiveMessage(message) {
        const chatList = this.shadow.getElementById("chatList");
        const chatItem = this.renderMessage(message);
        chatList.appendChild(chatItem);
        chatList.scrollTo(0, chatList.scrollHeight);
    }

    sendMessage() {
        const chatInput = this.shadow.getElementById("chatInput");
        const message = chatInput.value;
        if (message.length > 0) {
            send_message(this, message);
            const currentDate = new Date();
            const currentDateString = currentDate.toISOString().substring(0, 10);
            const chat = {
                senderName: localStorage.getItem("username"),
                message: message,
                date: currentDateString,
                isSent: true,
            };
            this.chats.push(chat);
            chatInput.value = "";
            this.receiveMessage(chat);
        }
    }
}

customElements.define("chat-room", ChatRoom);
