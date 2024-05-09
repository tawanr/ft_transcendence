from channels.db import database_sync_to_async as db_s2as
from .models import Chat, ChatRoom
from .utils_models import get_user_obj, get_blockUser_obj, get_room_obj
from django.utils import timezone
from .notification import check_notification
import json
import threading

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
		# time = time.strftime("%Y-%m-%d %H.%M.%S")
		time = time.strftime("%Y-%m-%d")
		chats_data.append({
			'senderName': chat.sender,
			'message': chat.content,
			'date': time,
			'isSent': chat.sender == self.user,
		})
	return chats_data

async def is_block(self, recipient, recipient_obj, sender_obj):
	recipient_block_obj = await get_blockUser_obj(recipient_obj, recipient)
	sender_block_obj = await get_blockUser_obj(sender_obj, self.sender)

	recipient_block = await db_s2as(recipient_block_obj.is_blocked_user)(self.sender)
	sender_block = await db_s2as(sender_block_obj.is_blocked_user)(recipient)

	is_block = sender_block or recipient_block

	return is_block

async def save_msg_history(self):
	print("In save_msg_history")
	room = await get_room_obj(self.room_name)
	sender_obj = await get_user_obj(self, self.sender)
	recipient_data = self.data.get("recipient")

	await self.save_massage(sender_obj, self.sender, room)

	is_group = True if isinstance(recipient_data, list) else False
	print(f"is_group: {is_group}")

	for member in recipient_data:
		print(f"member: {member}")
		recipient = member if is_group else recipient_data
		recipient_obj = await get_user_obj(self, recipient)

		if await is_block(self, recipient, recipient_obj, sender_obj):
			print("Block")
			if not is_group:
				break
			else:
				continue
		print("Not block!!!")
		await self.save_massage(recipient_obj, self.sender, room)
		await check_notification(recipient_obj, room)

		if not is_group:
			break

class ActiveUsers:
	room_users = {}
	lock = threading.Lock()

	@classmethod
	def add_user_to_room(cls, room_name, username):
		with cls.lock:
			if room_name not in cls.room_users:
				cls.room_users[room_name] = set()
			cls.room_users[room_name].add(username)

	@classmethod
	def remove_user_from_room(cls, room_name, username):
		with cls.lock:
			if room_name in cls.room_users:
				cls.room_users[room_name].discard(username)
				if not cls.room_users[room_name]:
					del cls.room_users[room_name]

	@classmethod
	def is_user_active_in_room(cls, room_name, username):
		with cls.lock:
			return room_name in cls.room_users and username in cls.room_users[room_name]
