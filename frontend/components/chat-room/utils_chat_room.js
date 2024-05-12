export function create_chat_socket() {
	const chatSocket = new WebSocket(
		'ws://127.0.0.1:8000' +
		'/ws/chatroom/room_tournament' +
		'/'
	)
	return chatSocket
}

export function websocket_event(context) {
	context.chatSocket.onopen = () => {
		open_chat_request(context);
		console.log('WebSocket connection established.');
		console.log("user: " + localStorage.getItem("username"))
	};

	context.chatSocket.onmessage = (e) => {
		if (!e.data)
			return
		const data = JSON.parse(e.data);
		if (data.type === "chat_history")
		{
			open_chat(context, data)
		}
		if (data.type === "message" && localStorage.getItem("username") !== data.sender) {
			receive_message(context, data)
		}
	}

	context.chatSocket.onclose = (event) => {
		console.log('WebSocket connection closed.', event);
	};

	context.chatSocket.onerror = (error) => {
		console.error('WebSocket error:', error);
	};
}

export function send_message(context, message) {
	// console.log("send_message")
	var sender = localStorage.getItem("username");
	//Temporaly use dummy as list of user in tournament, wait for real var from P'Tan
	var dummy = ["test_user55", "test_user2", "test_user3"];
	var recipient = []
	for (const user of dummy) {
		if (user !== sender)
			recipient.push(user)
	}
	// console.log("sender: " + sender)
	recipient.forEach(item => console.log(item));
	context.chatSocket.send(JSON.stringify({
		"message": message,
		"sender": sender,
		"recipient": recipient,
		"authorization" : localStorage.getItem("token") || null,
	}));
}

function open_chat_request(context) {
	context.chatSocket.send(JSON.stringify({
		"chat_history" : "True",
		"authorization" : localStorage.getItem("token") || null,
	}));
}

function open_chat(context, data) {
	context.chats = data.chats_data;
	context.render();
}

function receive_message(context, data) {
	const currentDate = new Date();
	const currentDateString = currentDate.toISOString().substring(0, 10);
	let currentSender = "";
	if (context.groupChat && data.sender !== currentSender) {
		currentSender = data.sender;
		const senderItem = document.createElement("div");
		senderItem.classList.add("chatSender");
		senderItem.innerHTML = currentSender;
		const chatList = context.shadow.getElementById("chatList");
		chatList.appendChild(senderItem);
	}
	const chat = {
		senderName: data.sender,
		message: data.message,
		date: currentDateString,
		isSent: false,
	};

	context.receiveMessage(chat);
}
