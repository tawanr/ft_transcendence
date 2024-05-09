from django.urls import path

from . import views

urlpatterns = [
    path("tournament/", views.user_tournament, name="user_tournament"),
    path(
        "tournament/player/",
        views.add_player_to_tournament,
        name="add_player_to_tournament",
    ),
    path(
        "tournament/<int:tournament_id>/",
        views.tournament_detail,
        name="tournament_detail",
    ),
    path(
        "tournament/<int:tournament_id>/join",
        views.join_tournament,
        name="join_tournament",
    ),
]
