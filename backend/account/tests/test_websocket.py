from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import path

from account.consumers import NotificationConsumer
from account.services import generate_user_token


class TestNotificationWebsocket(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.token, _ = generate_user_token(self.user)

    async def test_auth(self):
        application = URLRouter(
            [path("ws/notification/", NotificationConsumer.as_asgi())]
        )
        communicator = WebsocketCommunicator(application, "/ws/notification/")
        connected, subprotocol = await communicator.connect()
        assert connected
        data = {
            "type": "client.register",
            "authorization": "abc",
        }
        await communicator.send_json_to(data)
        message = await communicator.receive_json_from()
        self.assertEqual(message["type"], "disconnect")

    async def test_register(self):
        application = URLRouter(
            [path("ws/notification/", NotificationConsumer.as_asgi())]
        )
        communicator = WebsocketCommunicator(application, "/ws/notification/")
        connected, subprotocol = await communicator.connect()
        assert connected
        data = {
            "type": "client.register",
            "authorization": self.token,
        }
        await communicator.send_json_to(data)
        message = await communicator.receive_json_from()
        self.assertEqual(message["type"], "client.registered")
        await communicator.disconnect()
