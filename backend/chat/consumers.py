from channels.generic.websocket import AsyncWebsocketConsumer
# from django.contrib.auth.models import User
import json
from channels.db import database_sync_to_async
from django.utils.html import escape
from django.urls import reverse
import jwt
from django.conf import settings
from account.models import UserToken
from django.http import JsonResponse
from .models import ChatRoom, Chat
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class UserConsumer(AsyncWebsocketConsumer):
    # user: User = None

    def back_to_login(self):
        login_url = reverse("login")
        redirect_message = {
            "type": "redirect",
            "url": login_url
        }
        return redirect_message

    def get_owner_name(self, sender_username):
        if self.user == sender_username:
            return self.sender
        else:
            return self.recipient

    async def check_player_name(self):
        lst = [self.sender, self.recipient]
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
            return False
        return True

    async def ft_send_err(self, type, details):
        await self.send(text_data=json.dumps({
                "type": type,
                "details": details
        }))
        await self.close()

    async def check_authorization(self):
        print("In check_auth function!!!")
        # Extract JWT token from the Authorization header
        #Retrieve Authorization header from headers
        #Decodes the bytes obj value of the "Authorization" header into a UTF-8 str
        #converts the binary data into a human-readable string
        #b"" used to present byte literal, http headers name typically present as byte obj rather than str
        headers = self.scope.get("headers")
        # if not headers:
        #     return False
        authorization_header = None
        authFlag = False
        for header_name, header_value in headers:
            if header_name == b"authorization":
                authFlag = True
                authorization_header = header_value.decode("utf-8")
                break
        if authFlag is False:
            return
        print("authFlag is True")
        #Split value of Authorization header by space Bearer and token part
        #_ is placeholder for Bearer => not use anymore so discard it
        #jwt_token for token part
        try:
            bearer, jwt_token = authorization_header.split(" ")
        except ValueError:
            await self.ft_send_err("disconnect", "Invalid Authorization header for jwt")
            # return JsonResponse({"details": "Invalid authorization header format: Bearer token is missing"}, status=400)

        if bearer.lower() != "bearer":
            print("Wrong type of authorization header, it should be Bearer")
            await self.ft_send_err("disconnect", "Wrong type of authorization header: should be Bearer!!!")
            return

        if not jwt_token:
            # No token provided, close the connection
            print("No JWT token provided!!!")
            await self.ft_send_err("disconnect", "No JWT token provided!!!")
            return

        try:
            # Decode and verify the JWT token
            #decode_token with have key value as follow
            #sub: subject present user id
            #name: username
            #iat: issue at => time token was issued
            #exp: expiration time in unix time
            decoded_token = jwt.decode(jwt_token, settings.JWT_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            # Token has expired, close the connection
            print("JWT token has expired!!!")
            await self.ft_send_err("disconnect", "JWT token has expired!!!")
            return
        except jwt.InvalidTokenError:
            # Invalid token, close the connection
            print("Invalid JWT token!!!")
            await self.ft_send_err("disconnect", "Invalid JWT token!!!")
            return

        # Extract user ID from the decoded token
        # user_id = decoded_token.get("user_id")
        user_id = decoded_token["name"]
        # print("Decoded token:", decoded_token)
        self.user = user_id

        if not self.user:
            print("User is invalid!!!")
            await self.ft_send_err("disconnect", "User is invalid!!!")
            return

        print(f"Connect from user_id: {self.user}")

    async def connect(self):
        await self.accept()
        print("Connect to websocket!!!")
        self.user = None
        self.room_name = None
        # headers = self.scope.get("headers")
        # if headers:
        #     print("Have headers!!!")
        await self.check_authorization()

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        print(f"room_name is {self.room_name}")

        self.room_group_name = "chat_%s" % self.room_name
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

    async def save_massage(self, user, sender, message, room):
        # To create and save an object in a single step, use the create() method.
        await database_sync_to_async(Chat.objects.create)(
            user=user,
            room=room,
            # content=user + ": " + message,
            sender = sender,
            content= message,
        )

    async def get_user_obj(self, username):
        try:
            return await database_sync_to_async(User.objects.get)(username=username)  # Get the recipient user object
        except User.DoesNotExist:
            print(f"Invalid username: {username}")
            await self.ft_send_err("disconnect", f"Invalid username: {username}. Closing connection.")
            return None  # Return None if the user doesn't exist

    async def disconnect(self, close_code):
        #hasattr check if the self obj has the attribute room_group_name
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        print("\nIn receive function!!!")
        text_data_json = json.loads(text_data)
        connect = text_data_json.get("connect")
        # print(f"connect == auth: {connect}")

        if self.user:
            pass
        elif authorization := text_data_json.get("authorization"):
                print("Check authentication from json msg!!!")
                token = (
                    await UserToken.objects.filter(access_token=authorization)
                    .select_related("user")
                    .afirst()
                )
                if not token or not token.is_token_valid():
                    print("Token is invalid!!!!")
                    await self.ft_send_err("disconnect", "Unauthorized, invalid token. Closing connection.")
                    return JsonResponse({"details": "Unauthorized"}, status=401)
                else:
                    user = token.user
                    self.user = user.username
                    # print(f"User from json msg: {self.user}")
        else:
            print("Invalid authentication!!!")
            await self.ft_send_err("disconnect", "Invalid registration. Closing connection.")
            return

        print("Pass authentication!!!")
        if connect == text_data_json.get("authorization"):
            print("Connection from browser")
            return

        message = escape(text_data_json['message'])
        self.sender = text_data_json['sender']
        self.recipient = text_data_json['recipient']
        print(f"Sender name: {self.sender}")
        print(f"Recipient name: {self.recipient}\n")
        if (await self.check_player_name() is False):
            return
        # print(f"Message: {message}")

        #Find room obj
        print(f"room_name before get room form ChatRoom: {self.room_name}")
        # room = await database_sync_to_async(ChatRoom.objects.get)(name=self.room_name)
        room, _ = await database_sync_to_async(ChatRoom.objects.get_or_create)(
            name=self.room_name,
            defaults={"name": self.room_name}  # Defaults to use if the object is created
        )

        # print("Before get_user_obj")
        sender_obj = await self.get_user_obj(text_data_json["sender_username"])
        recipient_obj = await self.get_user_obj(text_data_json["recipient_username"])
        if not sender_obj or not recipient_obj:
            return JsonResponse({"details": "Invalid username"}, status=400)
            # return
        # print("After get_user_obj")

        self.owner_name = self.get_owner_name(text_data_json['sender_username'])
        await self.save_massage(sender_obj, self.sender, message, room)
        # print("After save_msg sender")
        await self.save_massage(recipient_obj, self.sender, message, room)
        # print("After save_msg recipinet")

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
        message = event['message']
        sender = event['sender']
        recipient = event['recipient']
        room = event['room']
        # chat_obj_all = await database_sync_to_async(Chat.objects.all)()
        chat_obj_all = await database_sync_to_async(
            # Chat.objects.select_related('room').all
            Chat.objects.select_related('room', 'user').order_by('timestamp').all
        )()

        print("After assign chat_obj_all function")

        async for chat in chat_obj_all:
            if (chat.room.name == room and chat.user.username == self.user):
                if (chat.sender != sender and chat.sender != recipient):
                    continue
                # print(f"{chat.timestamp}")
                time = chat.timestamp
                time = timezone.localtime(time)
                time = time.strftime("%Y-%m-%d %H.%M.%S")
                # print(f"{time}")
                # print(f"owner_name: {self.owner_name}")
                if self.owner_name == chat.sender:
                    self.print_chat(f"{time}")
                    self.print_chat(f"isSent: {True}")
                    self.print_chat(f"{chat.sender}: {chat.content}\n")
                else:
                    print(f"{time}")
                    print(f"isSent: {False}")
                    print(f"{chat.sender}: {chat.content}\n")

        # print(f"{sender} -> {recipient}: {message}")
        # print(f"{sender}: {message}")

        await self.send(text_data=json.dumps({
            "message" : message,
            "sender" : sender,
            "recipient" : recipient,
        }))

    def print_chat(self, msg):
        format_str = " " * 50 + msg
        print(format_str)
