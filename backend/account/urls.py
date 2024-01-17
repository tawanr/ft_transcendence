from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("refresh/", views.refresh_token_view, name="refresh_token"),
    path("user/", views.user_view, name="user"),
]
