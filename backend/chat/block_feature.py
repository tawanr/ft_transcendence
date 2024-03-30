from channels.db import database_sync_to_async as db_s2as
from .models import BlockUser
import json

async def group_send_block_req(self):
		await self.channel_layer.group_send(
			self.room_group_name,
			{
				"type" : "block_player",
				"sender": self.data.get("sender"),
				"sender_username": self.data.get("sender_username"),
				"block_username" : self.data.get("block_username"),
				"block_player" : self.data.get("block_player"),
				"channel_name" : self.channel_name,
				"status" : self.data.get("status")
			}
		)

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

async def block_player(self, event):
	print("In block user function!!!")

	sender_user_obj = await self.get_user_obj(event['sender_username'])
	sender_block_obj = await self.get_blockUser_obj(sender_user_obj, event['sender'])
	user_to_block = event['block_username']
	player_to_block = event['block_player']
	blocked_user_obj = await self.get_user_obj(user_to_block)
	# if user_to_block == self.user and channel_name == self.channel_name:
	#     await self.ft_send_err("disconnect", "Cannot block their own user. Closing connection.")
	#     return
	# elif user_to_block == self.user:
	#     player_to_block = event['sender']
	if player_to_block:
		if event['status'] == "unblock":
			print("In unblock condition!!!")
			if not await db_s2as(sender_block_obj.unblock_user)(blocked_user_obj, player_to_block):
				await self.ft_send_err("disconnect", f"Unable to unblock {player_to_block}, not in the blocked group. Closing connection.")
				return

			await self.send(text_data=json.dumps({
				"type": "success",
				"details": f"Successfully unblock player name {player_to_block}"
			}))
		else:
			if not await db_s2as(sender_block_obj.block_user)(blocked_user_obj, player_to_block):
				await self.ft_send_err("disconnect", f"Unable to block {player_to_block}, maybe already in the blocked group. Closing connection.")
				return

			await self.send(text_data=json.dumps({
				"type": "success",
				"details": f"Successfully block player name {player_to_block}"
			}))
	else:
		await self.ft_send_err("disconnect", "Invalid player name to block. Closing connection.")
