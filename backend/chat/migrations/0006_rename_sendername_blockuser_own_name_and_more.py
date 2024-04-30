# Generated by Django 5.0.1 on 2024-03-26 13:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0005_remove_chatroom_blocked_users_blockuser"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name="blockuser",
            old_name="senderName",
            new_name="own_name",
        ),
        migrations.AddField(
            model_name="blockuser",
            name="own_user",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="blockuser",
            name="blocked_users",
            field=models.ManyToManyField(
                blank=True, related_name="blocked_users", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
