from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.get_csrf, name="csrf"),
    path("register/", views.register_view, name="register"),
]
