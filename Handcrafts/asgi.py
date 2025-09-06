import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.security.websocket import AllowedHostsOriginValidator
from .midleware import TokenAuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Handcrafts.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            TokenAuthMiddleware(
                URLRouter([
                    # Combine all WebSocket URL patterns here
                    *notifications_ws_urlpatterns,
                    *chatapp_ws_urlpatterns,
                ])
            )
        ),
    }
)