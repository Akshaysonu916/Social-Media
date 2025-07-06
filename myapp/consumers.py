import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

# In-memory online user tracking
online_users = set()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        online_users.add(self.user.id)
        await self.broadcast_status("online")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        if self.user.is_authenticated and self.user.id in online_users:
            online_users.remove(self.user.id)
            await self.broadcast_status("offline")

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Typing indicator
        if 'typing' in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_event',
                    'typing': data['typing'],
                    'sender_id': self.user.id
                }
            )
            return

        # Sending message
        if 'message' in data:
            message_text = data['message']
            message_obj = await self.save_message(self.user, message_text)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_obj.content,
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,  # ✅ Add sender username
                    'timestamp': message_obj.timestamp.strftime("%H:%M"),
                    'message_id': message_obj.id,
                    'conversation_id': self.conversation_id  # ✅ Optional: for frontend logic
                }
            )

        # Delete message
        if 'delete_message_id' in data:
            message_id = data['delete_message_id']
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'delete_message',
                    'message_id': message_id
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',  # ✅ Important for frontend filter
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],  # ✅ Include username
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
            'conversation_id': event['conversation_id']
        }))

    async def typing_event(self, event):
        await self.send(text_data=json.dumps({
            'typing': event['typing'],
            'sender_id': event['sender_id'],
        }))

    async def broadcast_status(self, status):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'status_event',
                'status': status,
                'user_id': self.user.id
            }
        )

    async def status_event(self, event):
        await self.send(text_data=json.dumps({
            'status': event['status'],
            'user_id': event['user_id']
        }))

    async def delete_message(self, event):
        await self.send(text_data=json.dumps({
            'delete': True,
            'message_id': event['message_id']
        }))

    @database_sync_to_async
    def save_message(self, sender, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        return Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content
        )
