import json

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from backend.decorators import login_required_401
from gameplay.models import Tournament, TournamentPlayer

# Create your views here.

User = get_user_model()


@require_http_methods(["GET", "POST"])
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
        bracket = async_to_sync(tournament.bracket)()
        players = async_to_sync(tournament.get_players)()
        return JsonResponse(
            {
                "id": tournament.id,
                "size": tournament.size,
                "bracket": bracket,
                "players": players,
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
        bracket = async_to_sync(tournament.bracket)()
        players = async_to_sync(tournament.get_players)()
        return JsonResponse(
            {
                "id": tournament.id,
                "size": tournament.size,
                "bracket": bracket,
                "players": players,
            }
        )


@require_POST
@login_required_401
def join_tournament(request, tournament_id: int):
    user = request.user
    tournament = Tournament.objects.filter(pk=tournament_id, is_active=True).first()
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
async def add_player_to_tournament(request):
    try:
        payload = json.loads(request.body)
        username = payload.get("username")
        tournament = await Tournament.objects.aget(game_type="pong")

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
