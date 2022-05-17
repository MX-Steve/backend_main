from django.urls import re_path

from . import consumers
from . import host_consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'assets/v1/ws/(?P<id>\w+)$', host_consumers.ChatConsumer.as_asgi()),
]