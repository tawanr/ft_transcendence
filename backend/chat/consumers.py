from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User


class UserConsumer(AsyncWebsocketConsumer):
    user: User = None

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass
