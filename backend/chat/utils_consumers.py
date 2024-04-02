
def get_owner_name(self, sender_username):
	if self.user == sender_username:
		return self.sender
	else:
		return self.recipient

async def check_player_name(self, player1, player2):
	lst = [player1, player2]
	lst = sorted(lst)
	room = "room_" + lst[0] + "_" + lst[1]
	if room != self.room_name:
		wrong_player = None
		for x in lst:
			if (x not in self.room_name):
				wrong_player = x
				break
		print("Invalid player name!!!")
		await self.ft_send_err("disconnect", f"Invalid player: {wrong_player}. Closing connection.")
		raise self.CustomException("")

def print_chats_data(self):
	for chat in self.chats_data:
		print(f"sender: {chat['senderName']}")
		print(f"message: {chat['message']}")
		print(f"date: {chat['date']}")
		print(f"isSent: {chat['isSent']}\n")
