import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import User,ChatMessage
# --- 通知消费者 (用于 R1-k, R1-l) ---
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_message(self, event):
        # 收到来自 tasks.py 的推送数据
        await self.send(text_data=json.dumps(event["data"]))

# --- 聊天消费者 (用于 R1-g 实时沟通) ---
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 假设前端传来的 room_name 是 "1_2" (ID小的在前)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_user = self.scope["user"]
        
        # --- 核心：解析接收者 ID ---
        # 如果 room_name 是 "1_2"，而发送者 ID 是 1，那么接收者就是 2
        ids = self.room_name.split('_')
        recipient_id = ids[1] if str(sender_user.id) == ids[0] else ids[0]

        # 广播给前端展示（实时）
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_user.real_name
            }
        )

        # --- 核心：存入数据库（持久化） ---
        # 注意：这里传的是对象或ID，save_message 内部需要处理
        await self.save_message(sender_user.id, recipient_id, message)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender']
        }))

    # 包装同步操作为异步
    @database_sync_to_async
    def save_message(self, sender_id, recipient_id, message_text):
        # 通过 ID 获取模型实例并创建消息记录
        sender = User.objects.get(id=sender_id)
        recipient = User.objects.get(id=recipient_id)
        return ChatMessage.objects.create(
            sender=sender, 
            recipient=recipient, 
            message=message_text
        )