import binascii
import json
import time
from uuid import uuid4
import jwt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User

from account.forms import RegisterForm
from account.models import UserToken
from backend.decorators import login_required_401


@require_POST
def register_view(request):
    form = RegisterForm(json.loads(request.body))
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors})
    User.objects.create_user(**form.cleaned_data, is_active=True)
    return JsonResponse(form.cleaned_data)


@require_POST
def login_view(request):
    payload = json.loads(request.body)
    user = (
        User.objects.filter(username=payload["username"])
        .select_related("usertoken")
        .first()
    )
    if not user:
        return JsonResponse(
            {"success": False, "errors": {"username": "Username does not exist"}}
        )
    if not user.check_password(payload["password"]):
        return JsonResponse(
            {"success": False, "errors": {"password": "Invalid password"}}
        )

    if hasattr(user, "usertoken"):
        user.usertoken.delete()

    # Create JWT access token with expiration in 30 minutes
    token_claims = {
        "sub": user.id,
        "name": user.username,
        "iat": int(time.time()),
        "exp": int(time.time()) + (60 * 30),
    }
    access_token = jwt.encode(token_claims, "secret", algorithm="HS256")

    refresh_token = binascii.hexlify(uuid4().bytes).decode()
    rtn = {
        "access_token": access_token,
    }
    UserToken.objects.create(
        user=user, access_token=access_token, refresh_token=refresh_token
    )
    response = JsonResponse(rtn)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True)
    return response


@require_POST
@login_required_401
def logout_view(request):
    if hasattr(request.user, "usertoken"):
        request.user.usertoken.delete()
    return JsonResponse({"success": True})
