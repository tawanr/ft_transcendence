from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import path

from account.consumers import NotificationConsumer
from account.models import UserNotifications
from account.services import generate_user_token


class TestNotificationWebsocket(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.token, _ = generate_user_token(self.user)

    async def connect_ws(self):
        application = URLRouter(
            [path("ws/notification/", NotificationConsumer.as_asgi())]
        )
        self.communicator = WebsocketCommunicator(application, "/ws/notification/")
        connected, subprotocol = await self.communicator.connect()
        assert connected
        data = {
            "type": "client.register",
            "authorization": self.token,
        }
        await self.communicator.send_json_to(data)
        message = await self.communicator.receive_json_from()
        return self.communicator, message

    async def test_auth(self):
        application = URLRouter(
            [path("ws/notification/", NotificationConsumer.as_asgi())]
        )
        self.communicator = WebsocketCommunicator(application, "/ws/notification/")
        connected, subprotocol = await self.communicator.connect()
        assert connected
        data = {
            "type": "client.register",
            "authorization": "abc",
        }
        await self.communicator.send_json_to(data)
        message = await self.communicator.receive_json_from()
        self.assertEqual(message["type"], "disconnect")

    async def test_register(self):
        communicator, message = await self.connect_ws()
        self.assertEqual(message["type"], "client.registered")
        await communicator.disconnect()

    async def test_get_notifications(self):
        types = UserNotifications.NotificationTypes
        sender = await sync_to_async(User.objects.create_user)(
            username="testuser2", password="testpassword"
        )
        await UserNotifications.objects.acreate(
            user=self.user,
            type=types.PRIVATE_CHAT,
            referral=sender.id,
        )
        communicator, message = await self.connect_ws()
        message = {"type": "client.notifications", "authorization": self.token}
        await communicator.send_json_to(message)
        response = await communicator.receive_json_from()
        expected = {"type": "notification_list", "data": [{"notification": types.PRIVATE_CHAT, "isRead": False}]}
        self.assertDictEqual(response, expected)
        message = {"type": "client.read", "authorization": self.token}
        await communicator.send_json_to(message)
        response = await communicator.receive_json_from()
        expected = {"type": "notification_list", "data": [{"notification": types.PRIVATE_CHAT, "isRead": True}]}
        self.assertDictEqual(response, expected)

    async def test_get_notification(self):
        communicator, _ = await self.connect_ws()
        types = UserNotifications.NotificationTypes
        sender = await sync_to_async(User.objects.create_user)(
            username="testuser2", password="testpassword"
        )
        await UserNotifications.objects.acreate(
            user=self.user,
            type=types.PRIVATE_CHAT,
            referral=sender.id,
        )
        response = await communicator.receive_json_from()
        expected = {"type": "notification", "notification": types.PRIVATE_CHAT, "isRead": False}
        self.assertDictEqual(response, expected)
