from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
import json
from channels.db import database_sync_to_async
from django.utils.html import escape
from django.urls import reverse
import jwt
from django.conf import settings
from account.models import UserToken
from django.http import JsonResponse

class UserConsumer(AsyncWebsocketConsumer):
    user: User = None

    def back_to_login(self):
        login_url = reverse("login")
        redirect_message = {
            "type": "redirect",
            "url": login_url
        }
        return redirect_message

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
        _, jwt_token = authorization_header.split(" ")

        if not jwt_token:
            # No token provided, close the connection
            print("No JWT token provided!!!")
            await self.send(text_data=json.dumps("No JWT token provided!!!"))
            await self.close()
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
            # await self.send(text_data=json.dumps(self.back_to_login()))
            await self.send(text_data=json.dumps("JWT token has expired!!!"))
            await self.close()
            return
        except jwt.InvalidTokenError:
            # Invalid token, close the connection
            print("Invalid JWT token!!!")
            await self.send(text_data=json.dumps("Invalid JWT token!!!"))
            await self.close()
            return

        # Extract user ID from the decoded token
        # user_id = decoded_token.get("user_id")
        user_id = decoded_token["name"]
        # print("Decoded token:", decoded_token)
        self.user = user_id

        if not self.user:
            print("User is invalid!!!")
            await self.send(text_data=json.dumps("User is invalid!!!"))
            # await self.send(text_data=json.dumps(self.back_to_login()))
            await self.close()
            return

        print(f"Connect from user_id: {self.user}")

    async def connect(self):
        await self.accept()
        print("Connect to websocket!!!")
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

    # async def save_massage(self, user, sender, message, room):

    # async def get_user_obj(self, username):

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
                    await self.send(text_data=json.dumps({
                        "type": "disconnect",
                        "details": "Unauthorized, invalid token. Closing connection.",
                    }))
                    await self.close()
                    return JsonResponse({"details": "Unauthorized"}, status=401)
        else:
            print("Invalid authentication!!!")
            await self.send(text_data=json.dumps({
                "type": "disconnect",
                "details": "Invalid registration. Closing connection.",
            }))
            await self.close()
            return

        print("Pass authentication!!!")
        if connect == text_data_json.get("authorization"):
            print("Connection from browser")
            return

        message = escape(text_data_json['message'])
        sender_name = text_data_json['sender_name']
        recipient_name = text_data_json['recipient_name']
        print(f"Sender name: {sender_name}")
        print(f"Recipient name: {recipient_name}")
        print(f"Message: {message}")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type" : "chat_message",
                "message" : message,
                "sender" : sender_name,
                "recipient" : recipient_name
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        recipient = event['recipient']

        print(f"consumers.py => {sender} send message to {recipient} => message: {message}")

        await self.send(text_data=json.dumps({
            "message" : message,
            "sender" : sender,
            "recipient" : recipient,
        }))

