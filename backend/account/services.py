import binascii
import os
import time
from uuid import uuid4

import jwt
from django.contrib.auth.models import User

from account.models import UserToken


def handle_upload_avatar(f):
    file_path = f"uploads/avatars/{f.name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path


def generate_user_token(user: User) -> (str, str):
    token_claims = {
        "sub": user.id,
        "name": user.username,
        "iat": int(time.time()),
        "exp": int(time.time()) + (60 * 30),
    }
    access_token = jwt.encode(token_claims, "secret", algorithm="HS256")
    refresh_token = binascii.hexlify(uuid4().bytes).decode()

    UserToken.objects.create(
        user=user, access_token=access_token, refresh_token=refresh_token
    )

    return access_token, refresh_token


def get_user_by_token(token: str) -> User:
    token = UserToken.objects.filter(access_token=token).first()
    if not token or token.is_token_valid():
        return None
    return token.user


def check_user_ingame(user: User) -> bool:
    return user.gameplayer_set.filter(
        game_room__is_active=True, is_active=True
    ).exists()
