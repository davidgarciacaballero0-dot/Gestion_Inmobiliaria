import json
from channels.generic.websocket import AsyncWebsocketConsumer


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = _safe_int(self.scope['url_route']['kwargs'].get('chat_id'))
        if not self.chat_id:
            await self.close(code=4001)
            return

        self.room_group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def chat_message(self, event):
        action = event.get('action')
        await self.send(text_data=json.dumps({
            'action': action,
            'chat_id': event.get('chat_id', self.chat_id),
            'mensaje_id': event.get('mensaje_id'),
        }))

class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = _safe_int(self.scope['url_route']['kwargs'].get('user_id'))
        if not self.user_id:
            await self.close(code=4001)
            return

        self.room_group_name = f'user_{self.user_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def user_event(self, event):
        await self.send(text_data=json.dumps({
            'action': event.get('action'),
            'chat_id': event.get('chat_id'),
            'mensaje_id': event.get('mensaje_id'),
        }))
