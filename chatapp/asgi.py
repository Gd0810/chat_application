"""
ASGI config for chatapp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Set DJANGO_SETTINGS_MODULE and initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatapp.settings')
try:
    django.setup()
except Exception as e:
    print(f"Error during django.setup(): {e}")
    raise

# Import core.routing after django.setup()
import core.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            core.routing.websocket_urlpatterns
        )
    ),
})