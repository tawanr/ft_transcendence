# Create a signal handler that create the model UserDetails on creations of a User model.

# Path: backend/account/signals.py
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from account.models import UserDetails, UserFriendInvite, UserNotifications
from chat.models import Chat
from channels.layers import get_channel_layer

from gameplay.models import Tournament


@receiver(post_save, sender=User)
def create_user_details(sender, instance, created, **kwargs):
    if created:
        UserDetails.objects.create(user=instance)

@receiver(post_save, sender=Chat)
def chat_notification(sender, instance, created, **kwargs):
    if not created:
        return
    room = instance.room
    players = room.name.split("_")
    if players[0] == "tournament":
        return
    else:
        sender_id = instance.user.id
        receiver_id = 0
        for player in players:
            if sender_id != int(player):
                receiver_id = int(player)
        if not receiver_id:
            return
        receiver = User.objects.get(id=receiver_id)
        UserNotifications.objects.create(
            user=receiver,
            type="private_chat",
            referral=sender_id,
        )

@receiver(post_save, sender=UserFriendInvite)
def invite_notification(sender, instance, created, **kwargs):
    if not created:
        return
    sender = instance.from_user
    receiver = instance.to_user
    UserNotifications.objects.create(
        user=receiver,
        type="friend_invite",
        referral=sender.id,
    )
