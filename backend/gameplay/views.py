import json
import stat
import traceback

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.contrib.auth.models import User

from account.models import UserNotifications
from backend.decorators import login_required_401
from gameplay.models import GamePlayer, GameRoom, Tournament, TournamentPlayer

# Create your views here.

User = get_user_model()


@require_http_methods(["GET", "POST", "DELETE"])
@login_required_401
def user_tournament(request):
    if request.method == "POST":
        if not hasattr(request.user, "usertoken"):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Unauthorized, failed to create tournament",
                }
            )
        try:
            payload = json.loads(request.body)
            game_type = payload.get("game_type")

            if not game_type:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Failed to create tournament, invalid game_type",
                    }
                )

            # Create a new tournament object
            if TournamentPlayer.objects.filter(
                tournament__is_active=True,
                player=request.user,
            ).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"User already in a tournament: {game_type}",
                    },
                    status=400,
                )

            tournament = Tournament.objects.create(game_type=game_type)
            async_to_sync(tournament.set_host)(request.user)

            if tournament:
                return JsonResponse(
                    {"success": True, "message": "Tournament created successfully"},
                    status=201,
                )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"An error occurred: {str(e)}"}
            )
    elif request.method == "GET":
        player = (
            TournamentPlayer.objects.filter(
                player=request.user,
            )
            .order_by("-date_added")
            .select_related("tournament")
            .first()
        )
        if not player:
            return JsonResponse(
                {
                    "success": False,
                    "message": "User is not in any active tournament",
                },
                status=404,
            )
        tournament = player.tournament
        bracket = async_to_sync(tournament.bracket)()
        players = async_to_sync(tournament.get_players)()
        return JsonResponse(
            {
                "id": tournament.id,
                "size": tournament.size,
                "isHost": player.is_host,
                "isPlaying": tournament.is_playing,
                "isFinished": tournament.is_finished,
                "bracket": bracket,
                "players": players,
            }
        )
    elif request.method == "DELETE":
        player = (
            TournamentPlayer.objects.filter(
                player=request.user,
                is_active=True,
                tournament__is_active=True,
            )
            .select_related("tournament")
            .first()
        )
        if not player:
            return JsonResponse(
                {
                    "success": False,
                    "message": "User is not in any active tournament",
                },
                status=404,
            )
        tournament = player.tournament
        tournament.players.remove(request.user)
        return JsonResponse(
            {
                "success": True,
                "message": "User removed from tournament successfully",
            }
        )


@require_http_methods(["GET", "POST"])
@login_required_401
def tournament_detail(request, tournament_id: int):
    tournament = Tournament.objects.filter(id=tournament_id).first()
    if not tournament:
        raise Http404("Tournament not found")

    if request.method == "POST":
        if async_to_sync(tournament.get_host)() != request.user:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Unauthorized, only host can start tournament",
                },
                status=401,
            )
        if not async_to_sync(tournament.start_tournament)():
            return JsonResponse(
                {"success": False, "message": "Tournament not ready to start"},
                status=400,
            )
        return JsonResponse(
            {"success": True, "message": "Tournament started"},
        )
    elif request.method == "GET":
        if not TournamentPlayer.objects.filter(
            player=request.user,
        ).exists():
            return JsonResponse(
                {
                    "success": False,
                    "message": "User not in tournament",
                },
                status=404,
            )
        bracket = async_to_sync(tournament.bracket)()
        players = async_to_sync(tournament.get_players)()
        return JsonResponse(
            {
                "id": tournament.id,
                "size": tournament.size,
                "isPlaying": tournament.is_playing,
                "bracket": bracket,
                "players": players,
            }
        )


@require_POST
@login_required_401
def join_tournament(request, tournament_id: int):
    user = request.user
    tournament = Tournament.objects.filter(
        pk=tournament_id, is_active=True).first()
    if not tournament:
        return JsonResponse(
            {"success": False, "message": "Tournament not found"}, status=404
        )
    if TournamentPlayer.objects.filter(
        tournament__is_active=True,
        player=request.user,
    ).exists():
        return JsonResponse(
            {
                "success": False,
                "message": "User already in a tournament",
            },
            status=400,
        )
    player = async_to_sync(tournament.add_player)(user)
    if not player:
        return JsonResponse(
            {"success": False, "message": "Unable to add player"}, status=500
        )
    return JsonResponse(
        {"success": True, "message": "Player added to tournament successfully"}
    )


@require_POST
@login_required_401
def invite_game_player(request):
    try:
        payload = json.loads(request.body)
        name = payload.get("username")
        invitee = User.objects.get(username=name)
        user = request.user
        if GamePlayer.objects.filter(game_room__is_active=True, is_active=True, player__in=[user, invitee]):
            response = JsonResponse(
                {"success": False, "message": "Player already in a game"}
            )
            response.status_code = 403
            return response
        room = GameRoom.objects.create()
        async_to_sync(room.add_player)(user)
        async_to_sync(room.add_player)(invitee)
        UserNotifications.objects.create(
            type="game_invite",
            user=invitee,
            referral=user.id,
        )
        return JsonResponse(
            {"success": True, "code": room.game_code}
        )
    except:
        response = JsonResponse(
            {"success": False, "message": "Cannot start a game with the given players"}
        )
        response.status_code = 403
        print(traceback.format_exc())
        return response


@require_POST
@login_required_401
async def add_player_to_tournament(request, tournament_id: int):
    try:
        payload = json.loads(request.body)
        username = payload.get("username")
        tournament = await Tournament.objects.filter(
            id=tournament_id,
            is_active=True,
            is_playing=False,
            is_finished=False,
            game_type="pong",
        ).first()

        if not tournament:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Tournament not valid",
                },
                status=404,
            )

        user_obj = await User.objects.aget(username=username)

        # Check if the player is already added to the tournament
        if await TournamentPlayer.objects.filter(
            player=user_obj, tournament=tournament
        ).aexists():
            return JsonResponse(
                {
                    "success": False,
                    "message": f"User {user_obj.username} is already added to the tournament",
                }
            )

        # Create a new TournamentPlayer object and add the user to the tournament
        created = await tournament.add_player(user_obj)

        if created:
            return JsonResponse(
                {
                    "success": True,
                    "message": f"User {user_obj.username} add to tournament successfully",
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Failed to add User {user_obj.username} to tournament",
                }
            )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"An error occurred: {str(e)}"}
        )
