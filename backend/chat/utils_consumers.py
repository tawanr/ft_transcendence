
def get_owner_name(self, sender_username):
	if self.user == sender_username:
		return self.sender
	else:
		return self.recipient

def print_chats_data(self):
	for chat in self.chats_data:
		print(f"sender: {chat['senderName']}")
		print(f"message: {chat['message']}")
		print(f"date: {chat['date']}")
		print(f"isSent: {chat['isSent']}\n")
