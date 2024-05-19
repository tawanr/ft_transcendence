"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from account.routing import websocket_urlpatterns as account_urlpatterns
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import websocket_urlpatterns as chat_urlpatterns
from django.core.asgi import get_asgi_application
from gameplay.routing import websocket_urlpatterns as gameplay_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# application = ProtocolTypeRouter(
#     {
#         "http": get_asgi_application(),
#         "websocket": URLRouter(gameplay_urlpatterns + chat_urlpatterns),
#     }
# )

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(gameplay_urlpatterns + chat_urlpatterns + account_urlpatterns)
        ),
    }
)
