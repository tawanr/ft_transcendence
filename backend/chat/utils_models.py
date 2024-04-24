from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async as db_s2as
from .models import BlockUser, Chat

User = get_user_model()

async def get_user_obj(self, username):
	try:
		return await db_s2as(User.objects.get)(username=username)  # Get the recipient user object
	except User.DoesNotExist:
		print(f"Invalid username: {username}")
		await self.ft_send_err("disconnect", f"Invalid username: {username}. Closing connection.")
		raise self.CustomException("Invalid username", username)
		# return None  # Return None if the user doesn't exist

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

async def check_notification(self, sender, recipient):
	self.notification = 0
	ch_query = Chat.objects.filter(sender=sender)
	ch_obj = await db_s2as(ch_query.latest)('timestamp')

	if not self.active_channel.get(recipient):
		await ch_obj.assign_notification(True, sender)
	else:
		await ch_obj.assign_notification(False, sender)

	# self.notification = Chat.objects.filter(sender=sender, notification=True).count()
	self.notification = await db_s2as(Chat.objects.filter(sender=sender, notification=True).count)()
	# async for obj in Chat.objects.filter(sender=sender, notification=True):
	# 	self.notification += 1
