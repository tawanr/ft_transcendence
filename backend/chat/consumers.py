import json

from channels.db import database_sync_to_async as db_s2as
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils.html import escape

from .auth import check_authorization_header, check_authorization_payload
from .models import Chat
from .notification import clear_notification
from .utils_consumers import ActiveUsers as au
from .utils_consumers import display_chat_history, save_msg_history
from .utils_models import get_avatar_url, get_blockUser_obj, get_room_obj, get_user_obj

User = get_user_model()


class UserConsumer(AsyncWebsocketConsumer):
    async def ft_send_err(self, type, details):
        await self.send(text_data=json.dumps({"type": type, "details": details}))

    async def connect(self):
        await self.accept()
        self.user = None
        self.room_type = self.scope["url_route"]["kwargs"]["room_type"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_name = self.room_type

        try:
            await check_authorization_header(self)
        except Exception as e:
            self.ft_send_err("disconnect", str(e))
        if self.room_type == "tournament":
            self.room_name = f"{self.room_type}_{self.room_id}"
            self.room_group_name = "chat_%s" % self.room_name
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        elif self.room_type == "private":
            pass

    async def save_message(self, user, sender, room):
        # To create and save an object in a single step, use the create() method.
        await db_s2as(Chat.objects.create)(
            user=user,
            room=room,
            sender=sender,
            content=self.message,
        )

    async def disconnect(self, close_code):
        # hasattr check if the self obj has the attribute room_group_name
        if hasattr(self, "room_group_name"):
            au.remove_user_from_room(self.roomname, self.user)
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    def is_check_req(self, req_name):
        req = {}
        req["chat_history"] = {"chat_history", "authorization"}
        req["block"] = {
            "sender",
            "recipient",
            "authorization",
            "block",
            "chat_history",
            "connect",
        }
        req["unblock"] = {
            "sender",
            "recipient",
            "authorization",
            "unblock",
            "chat_history",
            "connect",
        }
        req["msg"] = {"message", "sender", "recipient", "authorization"}
        req["invite"] = {
            "sender",
            "recipient",
            "invite_user",
            "authorization",
            "invitation",
            "chat_history",
            "connect",
        }
        req["profile"] = {
            "sender",
            "recipient",
            "authorization",
            "profile",
            "chat_history",
            "connect",
        }

        data = set(self.data.keys())
        if data == req[req_name]:
            if req_name == "block" or req_name == "unblock":
                self.data["status"] = "block" if req_name == "block" else "unblock"
            return True
        return False

    async def receive(self, text_data):
        try:
            try:
                self.data = json.loads(text_data)
            except json.JSONDecodeError as e:
                await self.ft_send_err("disconnect", f"JSON message error: {e}")
                return

            await check_authorization_payload(self)

            if self.data.get("connect"):
                return

            req_dict = {
                "chat_history": self.send_chat_history,
                "block": self.group_send_block_req,
                "unblock": self.group_send_block_req,
                "msg": self.group_send_msg,
                "invite": self.invite_player,
                "profile": self.group_see_profile_req,
                # 'tournament' : 'tournament'
            }
            for req_type in req_dict:
                if self.is_check_req(req_type):
                    await req_dict[req_type]()
                    return
            await self.ft_send_err(
                "disconnect", "Invalid JSON payload. Closing connection."
            )
        except self.CustomException as e:
            if str(e) == "Unauthorized":
                return JsonResponse({"details": "Unauthorized"}, status=401)
            elif str(e) == "Invalid username":
                return JsonResponse(
                    {"details": f"Invalid username: {e.var}"}, status=400
                )
            else:
                return

    async def group_send_block_req(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "block_player",
                "sender": self.data.get("sender"),
                "recipient": self.data.get("recipient"),
                "channel_name": self.channel_name,
                "status": self.data.get("status"),
            },
        )

    async def block_player(self, event):
        sender_user_obj = await get_user_obj(self, event["sender"])
        sender_block_obj = await get_blockUser_obj(sender_user_obj, event["sender"])
        player_to_block = event["recipient"]
        player_to_block_obj = await get_user_obj(self, player_to_block)
        player_to_block_username = player_to_block_obj.username

        if player_to_block_username == self.user:
            await self.ft_send_err(
                "disconnect", "Cannot block their own user. Closing connection."
            )
            return
        if player_to_block:
            if event["status"] == "unblock":
                if not await db_s2as(sender_block_obj.unblock_user)(player_to_block):
                    await self.ft_send_err(
                        "disconnect",
                        f"Cannot unblock: {player_to_block} not in block groups. Close connection",
                    )
                    return

                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "success",
                            "details": f"Successfully unblock player name {player_to_block}",
                        }
                    )
                )
            else:
                if not await db_s2as(sender_block_obj.block_user)(player_to_block):
                    await self.ft_send_err(
                        "disconnect",
                        f"Cannot block: {player_to_block} is already in block groups. Close connection",
                    )
                    return

                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "success",
                            "details": f"Successfully block player name {player_to_block}",
                        }
                    )
                )
        else:
            await self.ft_send_err(
                "disconnect", "Invalid player name to block. Closing connection."
            )

    async def invite_player(self):
        self.data["message"] = (
            f"{self.data.get('sender')} invite {self.data.get('invite_user')} to play pong game"
        )
        await self.group_send_msg()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "success",
                    "details": f"Successfully send invitation to player name {self.data.get('recipient')}",
                }
            )
        )

    async def group_see_profile_req(self):
        sender = self.data["sender"]
        recipient = self.data["recipient"]

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "see_profile",
                "sender": sender,
                "recipient": recipient,
            },
        )
        await self.send(
            text_data=json.dumps(
                {
                    "type": "success",
                    "details": f"Successfully see profile of {recipient}",
                }
            )
        )

    async def see_profile(self, event):
        recipient_obj = await get_user_obj(self, event["recipient"])
        user = await db_s2as(User.objects.get)(id=recipient_obj.id)
        avatar = await db_s2as(get_avatar_url)(user)

        await self.send(
            text_data=json.dumps(
                {
                    "sender": event["sender"],
                    "recipient": event["recipient"],
                    "username": recipient_obj.username,
                    "email": recipient_obj.email,
                    "avatar": avatar,
                }
            )
        )

    async def group_send_msg(self):
        self.message = escape(self.data["message"])
        self.sender = self.data["sender"]
        self.recipient = self.data["recipient"]

        await save_msg_history(self)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": escape(self.data["message"]),
                "sender": self.data["sender"],
                "room": self.room_name,
            },
        )

    async def chat_message(self, event):
        self.sender = event["sender"]

        if not au.is_user_active_in_room(self.room_name, self.user):
            # await send_notification(self, self.user)
            return

        # Find room obj
        # room = await get_room_obj(event["room"])

        # self.chats_data = []
        # user = await get_user_obj(self, self.user)
        # chat_query = Chat.objects.filter(user=user, room=room).order_by("timestamp")
        # chat_obj_all = await db_s2as(chat_query.all)()

        # async for chat in chat_obj_all:
        #     time = chat.timestamp
        #     time = timezone.localtime(time)
        #     # time = time.strftime("%Y-%m-%d %H.%M.%S")
        #     time = time.strftime("%Y-%m-%d")

        #     self.chats_data.append(
        #         {
        #             "senderName": chat.sender,
        #             "message": chat.content,
        #             "date": time,
        #             "isSent": chat.sender == self.sender,
        #         }
        #     )

        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    # "chats_data": self.chats_data,
                    "message": event["message"],
                    "sender": self.sender,
                }
            )
        )

    async def send_notification(self, event):
        if self.channel_name != event["channel_name"]:
            return
        await self.send(
            text_data=json.dumps(
                {"notification": event["notification"], "user": event["user"]}
            )
        )

    async def send_chat_history(self):
        if self.data.get("chat_history") == "False":
            au.remove_user_from_room(self.room_name, self.user)
            return
        if self.room_type == "private":
            users = [int(self.user_id), int(self.room_id)]
            users.sort()
            self.room_name = str(users[0]) + "_" + str(users[1])
            self.room_group_name = "chat_%s" % self.room_name
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_history",
                    "chats_data": await display_chat_history(self),
                }
            )
        )
        au.add_user_to_room(self.room_name, self.user)
        await clear_notification(self, self.user)

    class CustomException(Exception):
        def __init__(self, message, var=None):
            super().__init__(message)
            self.var = var
