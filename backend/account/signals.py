# Create a signal handler that create the model UserDetails on creations of a User model.

# Path: backend/account/signals.py
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from account.models import UserDetails


@receiver(post_save, sender=User)
def create_user_details(sender, instance, created, **kwargs):
    if created:
        UserDetails.objects.create(user=instance)
