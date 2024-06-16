# Generated by Django 5.0.1 on 2024-06-14 14:37

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0003_userdetails_is_connected"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserNotifications",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("private_chat", "Private Chat"),
                            ("tour_chat", "Tour Chat"),
                            ("friend_invite", "Friend Invite"),
                            ("game_invite", "Game Invite"),
                            ("tour_invite", "Tour Invite"),
                            ("game_start", "Game Start"),
                            ("tour_round", "Tour Round"),
                        ],
                        max_length=20,
                    ),
                ),
                ("referral", models.CharField(max_length=30)),
                ("is_read", models.BooleanField(default=False)),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
