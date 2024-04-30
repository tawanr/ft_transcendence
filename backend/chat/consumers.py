from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async as db_s2as
from django.utils.html import escape
from django.http import JsonResponse
from .models import ChatRoom, Chat
from django.contrib.auth import get_user_model
from django.utils import timezone
from .auth import check_authorization_header, check_jwt
from .utils_models import get_blockUser_obj, get_user_obj, get_avatar_url, check_notification, clear_notification
from .utils_consumers import print_chats_data, display_chat_history
# from gameplay.models import GamePlayer as gp

User = get_user_model()

class UserConsumer(AsyncWebsocketConsumer):
    active_channel = {}

    async def ft_send_err(self, type, details):
        await self.send(text_data=json.dumps({
                "type": type,
                "details": details
        }))
        await self.close()

    async def connect(self):
        await self.accept()
        print("Connect to websocket!!!")
        self.user = None
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        print(f"room_name is {self.room_name}")

        await check_authorization_header(self)

        self.room_group_name = "chat_%s" % self.room_name
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

    async def save_massage(self, user, sender, recipient, room):
        # To create and save an object in a single step, use the create() method.
        await db_s2as(Chat.objects.create)(
            user=user,
            room=room,
            sender = sender,
            recipient = recipient,
            content= self.message,
        )

    async def disconnect(self, close_code):
        #hasattr check if the self obj has the attribute room_group_name
        if hasattr(self, 'room_group_name'):
            if UserConsumer.active_channel.get(self.user):
                del UserConsumer.active_channel[self.user]
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    def is_check_req(self, req_name):
        req = {}
        req['block'] = {'sender', 'recipient', 'authorization', 'block'}
        req['unblock'] = {'sender', 'recipient', 'authorization', 'unblock'}
        req['msg'] = {'message', 'sender', 'recipient', 'authorization'}
        req['invite'] = {'sender', 'recipient', 'authorization', 'invitation'}
        req['profile'] = {'sender', 'recipient', 'authorization', 'profile'}

        data = set(self.data.keys())
        if data == req[req_name]:
            if req_name == 'block' or req_name == 'unblock':
                self.data['status'] = 'block' if req_name == 'block' else 'unblock'
            return True
        return False

    async def receive(self, text_data):
        print("\nIn receive function!!!")
        try:
            try:
                self.data = json.loads(text_data)
            except json.JSONDecodeError as e:
                print("JSON message error:", e)
                await self.ft_send_err("disconnect", f"JSON message error: {e}")
                return

            if self.user:
                pass
            elif authorization := self.data.get("authorization"):
                self.user = await check_jwt(self, authorization)
            else:
                print("Invalid authentication!!!")
                await self.ft_send_err("disconnect", "Invalid registration. Closing connection.")
                return

            if (self.data.get("sender")):
                sender = self.data.get("sender")
                UserConsumer.active_channel[sender] = self.channel_name
                await clear_notification(self, self.user)

            print("Pass authentication!!!")
            if self.data.get("connect"):
                print("Connection from browser")
                await self.send(text_data=json.dumps({
                    "chats_data" : await display_chat_history(self),
                }))
                return

            req_dict = {
                'block' : self.group_send_block_req,
                'unblock' : self.group_send_block_req,
                'msg' : self.group_send_msg,
                'invite' : self.invite_player,
                'profile' : self.group_see_profile_req,
                # 'tournament' : 'tournament'
            }
            for req_type in req_dict:
                if self.is_check_req(req_type):
                    await req_dict[req_type]()
                    return
            await self.ft_send_err("disconnect", "Invalid JSON payload. Closing connection.")
        except self.CustomException as e:
            if str(e) == "Unauthorized":
                return JsonResponse({"details": "Unauthorized"}, status=401)
            elif str(e) == "Invalid username":
                return JsonResponse({"details": f"Invalid username: {e.var}"}, status=400)
            else:
                return


    async def group_send_block_req(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type" : "block_player",
                "sender": self.data.get("sender"),
                "recipient" : self.data.get("recipient"),
                "channel_name" : self.channel_name,
                "status" : self.data.get("status")
            }
        )

    async def block_player(self, event):
        sender_user_obj = await get_user_obj(self, event['sender'])
        sender_block_obj = await get_blockUser_obj(sender_user_obj, event['sender'])
        player_to_block = event['recipient']
        player_to_block_obj = await get_user_obj(self, player_to_block)
        player_to_block_username = player_to_block_obj.username

        if player_to_block_username == self.user:
            await self.ft_send_err("disconnect", "Cannot block their own user. Closing connection.")
            return
        if player_to_block:
            if event['status'] == "unblock":
                if not await db_s2as(sender_block_obj.unblock_user)(player_to_block):
                    await self.ft_send_err("disconnect", f"Cannot unblock: {player_to_block} not in block groups. Close connection")
                    return

                await self.send(text_data=json.dumps({
                    "type": "success",
                    "details": f"Successfully unblock player name {player_to_block}"
                }))
            else:
                if not await db_s2as(sender_block_obj.block_user)(player_to_block):
                    await self.ft_send_err("disconnect", f"Cannot block: {player_to_block} is already in block groups. Close connection")
                    return

                await self.send(text_data=json.dumps({
                    "type": "success",
                    "details": f"Successfully block player name {player_to_block}"
                }))
        else:
            await self.ft_send_err("disconnect", "Invalid player name to block. Closing connection.")

    async def invite_player(self):
        self.data['message'] = f"{self.data.get('sender')} invite you to play pong game"
        self.data['msg_type'] = "invitation"
        await self.group_send_msg()
        await self.send(text_data=json.dumps({
            "type": "success",
            "details": f"Successfully send invitation to player name {self.data.get('recipient')}"
        }))

    async def group_see_profile_req(self):
        sender = self.data['sender']
        recipient = self.data['recipient']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type" : "see_profile",
                "sender" : sender,
                "recipient" : recipient,
            }
        )
        await self.send(text_data=json.dumps({
            "type": "success",
            "details": f"Successfully see profile of {recipient}"
        }))

    async def see_profile(self, event):
        recipient_obj = await get_user_obj(self, event
        ['recipient'])
        user = await db_s2as(User.objects.get)(id=recipient_obj.id)
        avatar = await db_s2as(get_avatar_url)(user)
        # win = await gp.get_win(gp, recipient_obj)
        # loss = await gp.get_loss(gp, recipient_obj)

        await self.send(text_data=json.dumps({
            "sender": event['sender'],
            "recipient": event['recipient'],
            "username": recipient_obj.username,
            "email": recipient_obj.email,
            "avatar": avatar,
            # "win" : win,
            # "loss" : loss
        }))

    async def group_send_msg(self):
        self.message = escape(self.data['message'])
        self.sender = self.data['sender']
        self.recipient = self.data['recipient']
        sender_username = self.data['sender']
        recipient_username = self.data['recipient']

        #Find room obj
        room, _ = await db_s2as(ChatRoom.objects.get_or_create)(
            name=self.room_name,
            defaults={"name": self.room_name}  # Defaults to use if the object is created
        )

        sender_obj = await get_user_obj(self, sender_username)
        recipient_obj = await get_user_obj(self, recipient_username)
        sender_block_obj = await get_blockUser_obj(sender_obj, self.sender)
        recipient_block_obj = await get_blockUser_obj(recipient_obj, self.recipient)

        if self.data.get('msg_type') != "invitation":
            await self.save_massage(sender_obj, self.sender, self.recipient, room)
        if not await db_s2as(recipient_block_obj.is_blocked_user)(self.sender) and not await db_s2as(sender_block_obj.is_blocked_user)(self.recipient):
            print("Not block!!!")
            await self.save_massage(recipient_obj, self.sender, self.recipient, room)
        else:
            print("Block!!!!!!!")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type" : "chat_message",
                "message" : self.message,
                "sender" : self.sender,
                "recipient" : self.recipient,
                "room" : room.name,
            }
        )

    async def chat_message(self, event):
        sender = event['sender']
        recipient = event['recipient']
        room = event['room']
        self.chats_data = []
        chat_obj_all = await db_s2as(
            Chat.objects.select_related('room', 'user').order_by('timestamp').all
        )()

        async for chat in chat_obj_all:
            if (chat.room.name == room and chat.user.username == self.user):
                if (chat.sender != sender and chat.sender != recipient):
                    continue
                time = chat.timestamp
                time = timezone.localtime(time)
                time = time.strftime("%Y-%m-%d %H.%M.%S")

                self.chats_data.append({
                    'senderName': chat.sender,
                    'message': chat.content,
                    'date': time,
                    'isSent': chat.sender == sender,
                })

        print_chats_data(self.chats_data)
        ##Notification
        await check_notification(self, sender, recipient)

        await self.send(text_data=json.dumps({
            "chats_data" : self.chats_data,
            "notification" : self.notification
        }))

    class CustomException(Exception):
        def __init__(self, message, var=None):
            super().__init__(message)
            self.var = var

