from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/gameplay/(?P<room_name>\w+)/$", consumers.GameplayConsumer.as_asgi()),
    re_path(r"ws/gameplay/$", consumers.GameplayConsumer.as_asgi()),
]
