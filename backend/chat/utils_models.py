from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async as db_s2as
from .models import BlockUser

User = get_user_model()

async def get_user_obj(self, username):
	try:
		return await db_s2as(User.objects.get)(username=username)  # Get the recipient user object
	except User.DoesNotExist:
		print(f"Invalid username: {username}")
		await self.ft_send_err("disconnect", f"Invalid username: {username}. Closing connection.")
		raise self.CustomException("Invalid username", username)
		# return None  # Return None if the user doesn't exist

async def get_blockUser_obj(user, playerName):
	sender_block_obj, _ = await db_s2as(BlockUser.objects.get_or_create)(
		own_user=user,
		own_name=playerName,
		defaults={
			"own_user": user,
			"own_name": playerName
		}  # Defaults to use if the object is created
	)
	return sender_block_obj
