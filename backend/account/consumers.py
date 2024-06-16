import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.http import JsonResponse

from account.models import UserNotifications, UserToken

logger = logging.getLogger()


class NotificationConsumer(AsyncWebsocketConsumer):
    user = None

    async def connect(self):
        logger.info("Connected to notification websocket.")
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        authorization = data.get("authorization")

        if (
            not data["type"] == "client.register" or not authorization
        ) and not self.user:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "disconnect",
                        "details": "Invalid registration. Closing connection.",
                    }
                )
            )
            await self.close()
            return

        token = (
            await UserToken.objects.filter(access_token=authorization)
            .select_related("user")
            .afirst()
        )
        if not token or not token.is_token_valid():
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "disconnect",
                        "details": "Invalid token. Closing connection.",
                    }
                )
            )
            await self.close()
            return
        self.user = token.user
        if not data["type"] == "client.register":
            return
        await self.send(
            text_data=json.dumps(
                {
                    "type": "client.registered",
                    "username": self.user.username,
                }
            )
        )

    async def client_notifications(self, event):
        notifications = UserNotifications.objects.filter(user=self.user).all()[:10]
        rtn = []
        for noti in notifications:
            data = {
                "type": noti.type,
                "is_read": noti.is_read,
            }
            rtn.append(data)
        await self.send(text_data=json.dumps({"data": rtn}))
