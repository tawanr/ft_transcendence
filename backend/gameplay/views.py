import json
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from gameplay.models import Tournament, TournamentPlayer
from django.http import JsonResponse
from backend.decorators import login_required_401
from django.contrib.auth import get_user_model

# Create your views here.

User = get_user_model()

@require_POST
@login_required_401
def create_tournament(request):
	if not hasattr(request.user, "usertoken"):
		return JsonResponse({'success': False, 'message': 'Unauthorized, failed to create tournament'})
	try:
		payload = json.loads(request.body)
		game_type = payload.get('game_type')

		if not game_type:
			return JsonResponse({'success': False, 'message': 'Failed to create tournament, invalid game_type'})

		#Create a new tournament object
		_, created = Tournament.objects.get_or_create(game_type=game_type)

		if created:
			return JsonResponse({'success': True, 'message': 'Tournament created successfully'})
		else:
			return JsonResponse({'success': False, 'message': f'Tournament already exists with the given game_type: {game_type}'})
	except Exception as e:
		return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})

@require_POST
@login_required_401
def add_player_to_tournament(request):
	try:
		payload = json.loads(request.body)
		username = payload.get("username")
		tournament = Tournament.objects.get(game_type="pong")

		user_obj = User.objects.get(username=username)

		# Check if the player is already added to the tournament
		if TournamentPlayer.objects.filter(player=user_obj, tournament=tournament).exists():
			return JsonResponse({'success': False, 'message': f'User {user_obj.username} is already added to the tournament'})

		# Create a new TournamentPlayer object and add the user to the tournament
		created = TournamentPlayer.objects.create(player=user_obj, tournament=tournament)

		if created:
			return JsonResponse({'success': True, 'message': f'User {user_obj.username} add to tournament successfully'})
		else:
			return JsonResponse({'success': False, 'message': f'Failed to add User {user_obj.username} to tournament'})
	except Exception as e:
		return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})
