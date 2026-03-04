# core/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 先初始化 Django 的 ASGI (处理静态文件等)
django_asgi_app = get_asgi_application()

# 导入你的根路由
from .routing import application