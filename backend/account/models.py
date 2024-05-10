import time

import jwt
from django.conf import settings
from django.core.cache import cache
from django.db import models
from gameplay.models import GamePlayer


class UserToken(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    access_token = models.CharField(max_length=250, unique=True)
    refresh_token = models.CharField(max_length=50, unique=True)

    def refresh_access_token(self):
        self.access_token = self.encode_jwt()
        self.save()

    def is_token_valid(self):
        try:
            claims = jwt.decode(
                self.access_token, settings.JWT_KEY, algorithms=["HS256"]
            )
        except jwt.exceptions.ExpiredSignatureError:
            return False
        if claims["exp"] < int(time.time()):
            return False
        if claims["sub"] != self.user.id:
            return False
        return True

    def encode_jwt(self):
        claims = {
            "sub": self.user.id,
            "name": self.user.username,
            "iat": int(time.time()),
            "exp": int(time.time()) + (60 * 30),
        }
        token = jwt.encode(claims, settings.JWT_KEY, algorithm="HS256")
        return token


class UserDetails(models.Model):
    user = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, related_name="details"
    )
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    friends = models.ManyToManyField("self")
    is_connected = models.BooleanField(default=False)

    def serialize(self) -> dict:
        # status = "online" if self.is_connected else "offline"
        status = "online" if cache.get(self.user.id) else "offline"
        if GamePlayer.objects.filter(player=self.user, is_active=True).exists():
            status = "ingame"
        return {
            "playerName": self.user.username,
            "playerId": self.user.id,
            "avatar": self.avatar.url
            if self.avatar
            else "/uploads/avatars/42_Logo.png",
            "status": status,
        }


class UserFriendInvite(models.Model):
    from_user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="sent_invites"
    )
    to_user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="received_invites"
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["from_user", "to_user"]

    def accept(self):
        self.from_user.details.friends.add(self.to_user)
        self.delete()
