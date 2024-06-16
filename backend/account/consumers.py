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
            await self.channel_layer.group_send(
                self.group_name,
                data
            )
            return
        self.group_name = f"notification_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
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
        async for noti in notifications:
            data = {
                "notification": noti.type,
                "isRead": noti.is_read,
            }
            rtn.append(data)
        await self.send(text_data=json.dumps({"type": "notification_list", "data": rtn}))

    async def client_read(self, event):
        notifications = UserNotifications.objects.filter(user=self.user).all()
        await notifications.aupdate(is_read=True)

    async def client_send_notification(self, event):
        id = event["id"]
        notification = await UserNotifications.objects.filter(id=id).afirst()
        if not notification:
            return
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "notification": notification.type,
                    "isRead": notification.is_read,
                }
            )
        )