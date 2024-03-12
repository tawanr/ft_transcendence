from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/user/(?P<room_name>\w+)/?$", consumers.UserConsumer.as_asgi()),
    # re_path(r"ws/user/$", consumers.UserConsumer.as_asgi()),
]
