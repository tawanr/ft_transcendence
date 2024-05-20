import json
import threading

from channels.db import database_sync_to_async as db_s2as
from django.utils import timezone

from .models import Chat, ChatRoom
from .notification import check_notification
from .utils_models import get_blockUser_obj, get_room_obj, get_user_obj


def get_owner_name(self, sender_username):
    if self.user == sender_username:
        return self.sender
    else:
        return self.recipient


async def display_chat_history(self):
    chats_data = []
    room = await get_room_obj(self.room_name)
    chat_query = Chat.objects.filter(room=room)
    chat_objs = await db_s2as(chat_query.order_by("timestamp").all)()

    async for chat in chat_objs:
        time = chat.timestamp
        time = timezone.localtime(time)
        # time = time.strftime("%Y-%m-%d %H.%M.%S")
        time = time.strftime("%Y-%m-%d")
        chats_data.append(
            {
                "senderName": chat.sender,
                "message": chat.content,
                "date": time,
                "isSent": chat.sender == self.user,
            }
        )
    return chats_data


async def is_block(self, recipient, recipient_obj, sender_obj):
    recipient_block_obj = await get_blockUser_obj(recipient_obj, recipient)
    sender_block_obj = await get_blockUser_obj(sender_obj, self.sender)

    recipient_block = await db_s2as(recipient_block_obj.is_blocked_user)(self.sender)
    sender_block = await db_s2as(sender_block_obj.is_blocked_user)(recipient)

    is_block = sender_block or recipient_block

    return is_block


async def save_msg_history(self):
    room = await get_room_obj(self.room_name)
    sender_obj = await get_user_obj(self, self.sender)

    await self.save_message(sender_obj, self.sender, room)


class ActiveUsers:
    room_users = {}
    lock = threading.Lock()

    @classmethod
    def add_user_to_room(cls, room_name, username):
        with cls.lock:
            if room_name not in cls.room_users:
                cls.room_users[room_name] = set()
            cls.room_users[room_name].add(username)

    @classmethod
    def remove_user_from_room(cls, room_name, username):
        with cls.lock:
            if room_name in cls.room_users:
                cls.room_users[room_name].discard(username)
                if not cls.room_users[room_name]:
                    del cls.room_users[room_name]

    @classmethod
    def is_user_active_in_room(cls, room_name, username):
        with cls.lock:
            return room_name in cls.room_users and username in cls.room_users[room_name]
