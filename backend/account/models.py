from django.conf import settings
from django.db import models
import time
import jwt


class UserToken(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    access_token = models.CharField(max_length=250, unique=True)
    refresh_token = models.CharField(max_length=50, unique=True)

    def refresh_access_token(self):
        claims = {
            "sub": self.user.id,
            "name": self.user.username,
            "iat": int(time.time()),
            "exp": int(time.time()) + (60 * 30),
        }
        token = jwt.encode(claims, settings.JWT_KEY, algorithm="HS256")
        self.access_token = token
        self.save()
