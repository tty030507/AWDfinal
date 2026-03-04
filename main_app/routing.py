from django.urls import re_path
from . import consumers  # 确保你已经创建了 consumers.py

# 变量名必须完全匹配：websocket_urlpatterns
websocket_urlpatterns = [
    # 修复点：在 ws 前面加上 ^/ 确保从路径开头精准匹配 [cite: 74]
    re_path(r'^ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'^ws/chat/(?P<room_name>[\w.-]+)/$', consumers.ChatConsumer.as_asgi()),
]