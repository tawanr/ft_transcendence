# Generated by Django 5.0.1 on 2024-04-02 19:28

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("gameplay", "0003_playerusermap_consumer_name"),
    ]

    operations = [
        migrations.RenameField(
            model_name="playerusermap",
            old_name="consumer_name",
            new_name="channel_name",
        ),
    ]
