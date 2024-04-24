from channels.db import database_sync_to_async as db_s2as
from .models import Chat, ChatRoom
from .utils_models import get_user_obj
from django.utils import timezone

def get_owner_name(self, sender_username):
	if self.user == sender_username:
		return self.sender
	else:
		return self.recipient

def print_chats_data(chats_data):
	for chat in chats_data:
		print(f"sender: {chat['senderName']}")
		print(f"message: {chat['message']}")
		print(f"date: {chat['date']}")
		print(f"isSent: {chat['isSent']}\n")

async def display_chat_history(self):
	print("\nIn display chat history")
	chats_data = []
	room, _ = await db_s2as(ChatRoom.objects.get_or_create)(
		name=self.room_name,
		defaults={"name": self.room_name}
	)
	user = await get_user_obj(self, self.user)
	chat_query = Chat.objects.filter(user=user, room=room)
	chat_objs = await db_s2as(
		chat_query.order_by('timestamp').all
	)()

	async for chat in chat_objs:
		time = chat.timestamp
		time = timezone.localtime(time)
		time = time.strftime("%Y-%m-%d %H.%M.%S")
		chats_data.append({
			'senderName': chat.sender,
			'message': chat.content,
			'date': time,
			'isSent': chat.sender == self.user,
		})
	# print_chats_data(chats_data)
	return chats_data
