from django.test import TestCase

from django.contrib.auth.models import User
from django.urls import reverse

from account.models import UserNotifications
from account.services import generate_user_token


class TestGame(TestCase):
    def test_game_invite(self):
        self.user = User.objects.create_user("test_user")
        self.invitee = User.objects.create_user("invitee")

        url = reverse("game_invite")
        token, _ = generate_user_token(self.user)

        payload = {"username": "invitee"}
        response = self.client.post(
            url,
            payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        notification = UserNotifications.objects.filter(
            user=self.invitee).count()
        self.assertEqual(notification, 1)

        response = self.client.post(
            url,
            payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)
