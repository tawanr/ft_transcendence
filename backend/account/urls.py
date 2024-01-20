from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("refresh/", views.refresh_token_view, name="refresh_token"),
    path("user/", views.user_view, name="user"),
    path("friends/", views.FriendsView.as_view(), name="friends"),
    path("friends/accept/", views.accept_friend_invite_view, name="invite_accept"),
    path("history/", views.list_game_history, name="history_list"),
]
