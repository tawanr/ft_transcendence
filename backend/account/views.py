import binascii
import json
import time
from uuid import uuid4
from xml.dom.domreg import registered

import jwt
from django.contrib.auth.models import User
from django.db.models import Case, Count, F, OuterRef, Q, Subquery, Value, When
from django.db.models.lookups import Exact
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_GET, require_POST
from gameplay.models import GameRoom

from account.forms import RegisterForm, UploadAvatarForm
from account.models import UserFriendInvite, UserToken
from account.services import handle_upload_avatar
from backend.decorators import login_required_401


@require_GET
@login_required_401
def user_view(request):
    user = User.objects.get(id=request.user.id)
    return JsonResponse(
        {
            "username": user.username,
            "email": user.email,
            "avatar": user.details.avatar.url if user.details.avatar else "",
        }
    )


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


@require_POST
def refresh_token_view(request):
    token = get_object_or_404(
        UserToken, refresh_token=request.COOKIES.get("refresh_token")
    )
    token.refresh_access_token()
    return JsonResponse({"access_token": token.access_token})


@method_decorator(login_required_401, name="dispatch")
class FriendsView(View):
    def get(self, request):
        friends = request.user.details.friends.all()
        return JsonResponse(
            {
                "data": [
                    {
                        "playerName": friend.user.username,
                        "playerId": friend.user.id,
                        "avatar": friend.avatar.url if friend.avatar else "",
                        "status": "online",
                    }
                    for friend in friends
                ]
            }
        )

    def post(self, request):
        payload = json.loads(request.body)
        friend = User.objects.filter(username=payload["username"]).first()
        if not friend:
            return JsonResponse(
                {"success": False, "errors": {"username": "Username does not exist"}},
                status=400,
            )
        if friend == request.user.details:
            return JsonResponse(
                {"success": False, "errors": {"username": "Cannot add yourself"}},
                status=400,
            )
        if friend in request.user.details.friends.all():
            return JsonResponse(
                {"success": False, "errors": {"username": "Already friends"}},
                status=400,
            )
        if UserFriendInvite.objects.filter(
            from_user=request.user, to_user=friend
        ).exists():
            return JsonResponse(
                {"success": False, "errors": {"username": "Invite already sent"}}
            )
        UserFriendInvite.objects.create(from_user=request.user, to_user=friend)
        return JsonResponse({"success": True, "details": "Invite sent"})


@login_required_401
@require_POST
def accept_friend_invite_view(request):
    payload = json.loads(request.body)
    inviter = get_object_or_404(User, username=payload["username"])
    invite = get_object_or_404(
        UserFriendInvite, from_user=inviter, to_user=request.user
    )
    invite.to_user.details.friends.add(invite.from_user.details)
    invite.delete()
    return JsonResponse({"success": True})


@login_required_401
@require_GET
def list_game_history(request):
    qs_get_player1_avatar = Case(
        When(
            Q(player1_name=request.user.username),
            then=Value(
                request.user.details.avatar.url if request.user.details.avatar else ""
            ),
        ),
        When(
            Count("players") == 2,
            then=Subquery(
                User.objects.get(username=OuterRef("player1_name")).values("avatar")[:1]
            ),
        ),
    )
    qs_history = (
        GameRoom.objects.filter(players__in=[request.user])
        .order_by("-created_date")
        .annotate(
            is_winner=Case(
                When(
                    Q(player1_name=request.user.username) & Q(player1_won=True),
                    then=Value(True),
                ),
                When(
                    Q(player2_name=request.user.username) & Q(player1_won=False),
                    then=Value(True),
                ),
                default=Value(False),
            ),
            player1_avatar=qs_get_player1_avatar,
            # registered_players=Count("players"),
            # opponent=When(
            #     Exact(Count("players"), 2),
            #     then=F(
            #         Subquery(
            #             GameRoom.objects.get(id=OuterRef("pk"))
            #             .players.exclude(username=request.user.username)
            #             .values("username")[:1]
            #         ),
            #     ),
            # ),
        )
    )
    return JsonResponse(
        {
            "data": [
                {
                    "player1Name": game.player1_name,
                    "player2Name": game.player2_name,
                    "isFinished": game.is_finished,
                    "score": f"{game.player1_score} - {game.player2_score}",
                    "isWinner": game.is_winner,
                    "date": game.created_date,
                    "playerCount": game.player_count,
                    "opponent": game.opponent,
                }
                for game in qs_history
            ]
        }
    )


@login_required_401
@require_POST
def avatar_upload_view(request):
    form = UploadAvatarForm(request.POST, request.FILES)
    if form.is_valid():
        file_path = handle_upload_avatar(request.FILES["image"])
        request.user.details.avatar = file_path
        request.user.details.save()
        return JsonResponse(
            {"success": True, "image_path": request.user.details.avatar.url}
        )
    return JsonResponse({"success": False, "errors": form.errors})
