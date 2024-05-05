from channels.db import database_sync_to_async as db_s2as
from .models import Chat, ChatRoom
from .utils_models import get_user_obj, get_blockUser_obj, get_room_obj
from django.utils import timezone
from .notification import check_notification
import json

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
	# print("\nIn display chat history")
	chats_data = []
	room = await get_room_obj(self.room_name)
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
	return chats_data

async def not_block(self, recipient, recipient_obj, sender_obj):
	recipient_block_obj = await get_blockUser_obj(recipient_obj, recipient)
	sender_block_obj = await get_blockUser_obj(sender_obj, self.sender)

	return not await db_s2as(recipient_block_obj.is_blocked_user)(self.sender) and not await db_s2as(sender_block_obj.is_blocked_user)(recipient)

async def save_msg_history(self):
	print("In save_msg_history")
	room = await get_room_obj(self.room_name)
	sender_obj = await get_user_obj(self, self.sender)
	recipient_data = self.data.get("recipient")

	await self.save_massage(sender_obj, self.sender, room)

	is_group = True if isinstance(recipient_data, list) else False
	print(f"is_group: {is_group}")

	for member in recipient_data:
		recipient = member if is_group else recipient_data
		recipient_obj = await get_user_obj(self, recipient)

		if await not_block(self, recipient, recipient_obj, sender_obj):
			print("Not block!!!")
			await self.save_massage(recipient_obj, self.sender, room)
			await check_notification(self, recipient_obj, room)
		else:
			print("Block!!!!!!!")
		if not is_group:
			break
