import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        print(f"WebSocket connected to room: {self.room_group_name}, user: {self.scope['user']}")
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # Broadcast online status
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'status_update', 'user': self.scope['user'].username, 'status': 'online'}
        )
        await self.accept()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected from room: {self.room_group_name}, code: {close_code}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # Broadcast offline status
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'status_update', 'user': self.scope['user'].username, 'status': 'offline'}
        )

    async def receive(self, text_data):
        print(f"Received WebSocket message: {text_data}")
        text_data_json = json.loads(text_data)
        if 'typing' in text_data_json:
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'typing_event', 'user': self.scope['user'].username, 'typing': text_data_json['typing']}
            )
            return
        if 'file' in text_data_json:
            profile = await database_sync_to_async(lambda: self.scope['user'].profile)()
            image_url = await database_sync_to_async(lambda: profile.image.url if profile.image else None)()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': text_data_json['message'],
                    'user': self.scope['user'].username,
                    'file': text_data_json['file'],
                    'image': image_url,
                }
            )
            return
        message = text_data_json['message']
        await self.save_message(self.scope['user'].username, self.room_name, message)
        profile = await database_sync_to_async(lambda: self.scope['user'].profile)()
        image_url = await database_sync_to_async(lambda: profile.image.url if profile.image else None)()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.scope['user'].username,
                'image': image_url,
            }
        )

    async def chat_message(self, event):
        print(f"Broadcasting message: {event['message']} from {event['user']}")
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user': event['user'],
            'file': event.get('file', None),
            'image': event.get('image', None),  # Include image
        }))

  
    async def typing_event(self, event):
        await self.send(text_data=json.dumps({
            'typing': event['typing'],
            'user': event['user'],
        }))

    async def status_update(self, event):
        await self.send(text_data=json.dumps({
            'status': event['status'],
            'user': event['user'],
        }))

    @database_sync_to_async
    def save_message(self, username, room_name, message):
        print(f"Saving message from {username} in room {room_name}: {message}")
        user = User.objects.get(username=username)
        Message.objects.create(room=room_name, sender=user, content=message)