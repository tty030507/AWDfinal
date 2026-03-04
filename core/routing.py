# core/routing.py
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import main_app.routing 

# 核心修复：必须包含 http 处理器 [cite: 4, 21]
application = ProtocolTypeRouter({
    # 处理普通的 HTTP 请求（API、网页、静态文件）
    "http": get_asgi_application(), 
    
    # 处理 WebSocket 请求 (用于 R1-g 聊天和实时通知) [cite: 23, 63]
    "websocket": AuthMiddlewareStack(
        URLRouter(
            main_app.routing.websocket_urlpatterns
        )
    ),
})