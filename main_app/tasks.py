# main_app/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification, User
from .serializers import NotificationSerializer

@shared_task
def send_notification_task(user_ids, message):
    """
    user_ids: 可以是单个 ID 或 ID 列表
    message: 通知内容
    """
    if isinstance(user_ids, int):
        user_ids = [user_ids]

    channel_layer = get_channel_layer()

    for uid in user_ids:
        # 1. 持久化到数据库
        note = Notification.objects.create(recipient_id=uid, message=message)
        
        # 2. 尝试推送 WebSocket (R1-g)
        async_to_sync(channel_layer.group_send)(
            f"user_{uid}", 
            {
                "type": "notification_message",
                "data": NotificationSerializer(note).data
            }
        )