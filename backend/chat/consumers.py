from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
import json
from channels.db import database_sync_to_async
from django.utils.html import escape
from django.urls import reverse
import jwt
from django.conf import settings

class UserConsumer(AsyncWebsocketConsumer):
    user: User = None

    def back_to_login(self):
        login_url = reverse("login")
        redirect_message = {
            "type": "redirect",
            "url": login_url
        }
        return redirect_message

    async def connect(self):
        await self.accept()
        print("Connect to websocket!!!")
        self.room_name = None
        # Extract JWT token from the Authorization header
        #Retrieve Authorization header from headers
        #Decodes the bytes obj value of the "Authorization" header into a UTF-8 str
        #converts the binary data into a human-readable string
        #b"" used to present byte literal, http headers name typically present as byte obj rather than str
        headers = self.scope.get("headers")
        # authorization_header = self.scope.get("headers").get(b"authorization").decode("utf-8")
        authorization_header = None
        for header_name, header_value in headers:
            if header_name == b"authorization":
                authorization_header = header_value.decode("utf-8")
                break
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
        print("Decoded token:", decoded_token)
        self.user = user_id

        if not self.user:
            print("User is invalid!!!")
            await self.send(text_data=json.dumps("User is invalid!!!"))
            # await self.send(text_data=json.dumps(self.back_to_login()))
            await self.close()
            return

        print(f"User id is: {self.user}")
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        print(f"room_name is {self.room_name}")

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        print("In receive function!!!")
        text_data_json = json.loads(text_data)
        message = escape(text_data_json['message'])
        print(f"Message is {message}")
