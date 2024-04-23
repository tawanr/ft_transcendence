from django.urls import path

from . import views

urlpatterns = [
	path("create_tournament/", views.create_tournament, name="create_tournament"),
	path("add_player_to_tournament/", views.add_player_to_tournament, name="add_player_to_tournament"),
]
