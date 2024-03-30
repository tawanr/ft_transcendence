from channels.generic.websocket import AsyncWebsocketConsumer
# from django.contrib.auth.models import User
import json
from channels.db import database_sync_to_async as db_s2as
from django.utils.html import escape
# from django.urls import reverse
# import jwt
# from django.conf import settings
# from account.models import UserToken
from django.http import JsonResponse
from .models import ChatRoom, Chat
from django.contrib.auth import get_user_model
from django.utils import timezone
from .auth import check_authorization_header, check_jwt
from .utils_models import get_blockUser_obj, get_user_obj

User = get_user_model()

class UserConsumer(AsyncWebsocketConsumer):
    def get_owner_name(self, sender_username):
        if self.user == sender_username:
            return self.sender
        else:
            return self.recipient

    async def check_player_name(self, player1, player2):
        lst = [player1, player2]
        lst = sorted(lst)
        room = "room_" + lst[0] + "_" + lst[1]
        if room != self.room_name:
            wrong_player = None
            for x in lst:
                if (x not in self.room_name):
                    wrong_player = x
                    break
            print("Invalid player name!!!")
            await self.ft_send_err("disconnect", f"Invalid player: {wrong_player}. Closing connection.")
            raise self.CustomException("")

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
        self.room_name = None
        # await self.check_authorization_header()
        await check_authorization_header(self)

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        print(f"room_name is {self.room_name}")

        self.room_group_name = "chat_%s" % self.room_name
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

    async def save_massage(self, user, sender, message, room):
        # To create and save an object in a single step, use the create() method.
        await db_s2as(Chat.objects.create)(
            user=user,
            room=room,
            # content=user + ": " + message,
            sender = sender,
            content= message,
        )

    async def disconnect(self, close_code):
        #hasattr check if the self obj has the attribute room_group_name
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    def is_check_req(self, req_name):
        req = {}
        req['block'] = {'sender', 'sender_username', 'block_username', 'block_player', 'authorization', 'block'}
        req['unblock'] = {'sender', 'sender_username', 'block_username', 'block_player', 'authorization', 'unblock'}
        req['msg'] = {'message', 'sender', 'recipient', 'sender_username', 'recipient_username', 'authorization'}
        req['invite'] = {'invite_user', 'invite_player', 'authorization'}
        for k in self.data:
            if k not in req[req_name]:
                return False
        if req_name == 'block' or req_name == 'unblock':
            self.data['status'] = 'block' if req_name == 'block' else 'unblock'
        return True

    async def receive(self, text_data):
        print("\nIn receive function!!!")
        try:
            try:
                self.data = json.loads(text_data)
            except json.JSONDecodeError as e:
                print("JSON message error:", e)
                await self.ft_send_err("disconnect", f"JSON message error: {e}")
                return
            connect = self.data.get("connect")

            # print(f"user: {self.user}")
            if self.user:
                pass
            elif authorization := self.data.get("authorization"):
                self.user = await check_jwt(self, authorization)
            else:
                print("Invalid authentication!!!")
                await self.ft_send_err("disconnect", "Invalid registration. Closing connection.")
                return

            print("Pass authentication!!!")
            if connect == self.data.get("authorization"):
                print("Connection from browser")
                return

            req_dict = {
                'block' : self.group_send_block_req,
                'unblock' : self.group_send_block_req,
                'msg' : self.receive_msg,
                'invite' : 'self.invite_user',
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
                "sender_username": self.data.get("sender_username"),
                "block_username" : self.data.get("block_username"),
                "block_player" : self.data.get("block_player"),
                "channel_name" : self.channel_name,
                "status" : self.data.get("status")
            }
        )

    async def block_player(self, event):
        print("In block user function!!!")

        # sender_user_obj = await self.get_user_obj(event['sender_username'])
        # sender_block_obj = await self.get_blockUser_obj(sender_user_obj, event['sender'])
        sender_user_obj = await get_user_obj(self, event['sender_username'])
        sender_block_obj = await get_blockUser_obj(sender_user_obj, event['sender'])
        player_to_block = event['block_player']

        if event['block_username'] == self.user:
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

    async def receive_msg(self):
        print("In receive msg function")
        message = escape(self.data['message'])
        self.sender = self.data['sender']
        self.recipient = self.data['recipient']
        self.owner_name = self.get_owner_name(self.data['sender_username'])
        print(f"Sender name: {self.sender}")
        print(f"Recipient name: {self.recipient}\n")
        await self.check_player_name(self.sender, self.recipient)

        #Find room obj
        print(f"room_name before get room form ChatRoom: {self.room_name}")
        room, _ = await db_s2as(ChatRoom.objects.get_or_create)(
            name=self.room_name,
            defaults={"name": self.room_name}  # Defaults to use if the object is created
        )

        # sender_obj = await self.get_user_obj(self.data["sender_username"])
        # recipient_obj = await self.get_user_obj(self.data["recipient_username"])
        # sender_block_obj = await self.get_blockUser_obj(sender_obj, self.sender)
        # recipient_block_obj = await self.get_blockUser_obj(recipient_obj, self.recipient)
        sender_obj = await get_user_obj(self, self.data["sender_username"])
        recipient_obj = await get_user_obj(self, self.data["recipient_username"])
        sender_block_obj = await get_blockUser_obj(sender_obj, self.sender)
        recipient_block_obj = await get_blockUser_obj(recipient_obj, self.recipient)

        await self.save_massage(sender_obj, self.sender, message, room)
        if not await db_s2as(recipient_block_obj.is_blocked_user)(self.sender) and not await db_s2as(sender_block_obj.is_blocked_user)(self.recipient):
            print("Not block!!!")
            await self.save_massage(recipient_obj, self.sender, message, room)
        else:
            print("Block!!!!!!!")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type" : "chat_message",
                "message" : message,
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
                    'date': time,
                    'isSent': chat.sender == sender,
                    'senderName': chat.sender,
                    'message': chat.content,
                })

        self.print_chats_data()

        await self.send(text_data=json.dumps({
            "chats_data" : self.chats_data
        }))

    def print_chats_data(self):
        for chat in self.chats_data:
            print(f"sender: {chat['senderName']}")
            print(f"message: {chat['message']}")
            print(f"date: {chat['date']}")
            print(f"isSent: {chat['isSent']}\n")

    class CustomException(Exception):
        def __init__(self, message, var=None):
            super().__init__(message)
            self.var = var

