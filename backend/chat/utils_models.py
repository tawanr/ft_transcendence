from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async as db_s2as
from .models import BlockUser, ChatRoom, Notification

User = get_user_model()

async def get_user_obj(self, username):
	try:
		return await db_s2as(User.objects.get)(username=username)  # Get the recipient user object
	except User.DoesNotExist:
		print(f"Invalid username: {username}")
		await self.ft_send_err("disconnect", f"Invalid username: {username}. Closing connection.")
		raise self.CustomException("Invalid username", username)
		# return None  # Return None if the user doesn't exist

async def get_room_obj(room_name):
	room, _ = await db_s2as(ChatRoom.objects.get_or_create)(
		name=room_name,
		defaults={"name": room_name}  # Defaults to use if the object is created
	)
	return room

async def get_noti_obj(user_obj, room_obj):
	noti, _ = await db_s2as(Notification.objects.get_or_create)(
			user=user_obj,
			room=room_obj,
			defaults={"user": user_obj, "room": room_obj}
		)
	return noti

async def get_blockUser_obj(user, username):
	sender_block_obj, _ = await db_s2as(BlockUser.objects.get_or_create)(
		own_user=user,
		own_username=username,
		defaults={
			"own_user": user,
			"own_username": username
		}  # Defaults to use if the object is created
	)
	return sender_block_obj

def get_avatar_url(user):
    return user.details.avatar.url if user.details.avatar else ""
