# Generated by Django 5.0.1 on 2024-04-04 18:52

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0008_remove_blockuser_blocked_users"),
    ]

    operations = [
        migrations.RenameField(
            model_name="blockuser",
            old_name="blocked_players",
            new_name="blocked_users",
        ),
        migrations.RenameField(
            model_name="blockuser",
            old_name="own_name",
            new_name="own_username",
        ),
    ]
