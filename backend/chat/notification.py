from channels.db import database_sync_to_async as db_s2as
from .models import ChatRoom, Notification
from .utils_models import get_noti_obj, get_user_obj, get_room_obj

def is_active_user(self, username):
	return self.active_channel.get(username) == self.room_name

async def check_notification(self, user_obj, room):
	username = user_obj.username
	if not is_active_user(self, username):
		noti = await get_noti_obj(user_obj, room)
		noti.notification += 1
		await noti.asave()

async def send_notification(self, recipient):
	print("In send notification")
	recipient_obj = await get_user_obj(self, recipient)
	room_obj = await get_room_obj(self.room_name)

	noti = await get_noti_obj(recipient_obj, room_obj)
	noti_count = noti.notification

	if noti_count > 0:
		await self.channel_layer.group_send(
			self.room_group_name,
			{
				"type" : "send_notification",
				"notification" : noti_count,
				"user" : self.user,
				"channel_name" : self.channel_name,
			}
		)

async def clear_notification(self, username):
	user_obj = await get_user_obj(self, username)
	room = await get_room_obj(self.room_name)
	noti, _ = await db_s2as(Notification.objects.get_or_create)(
			user=user_obj,
			room=room,
			defaults={"user": user_obj, "room": room}
		)
	noti.notification = 0
	await noti.asave()
