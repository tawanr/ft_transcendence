# Generated by Django 5.0.1 on 2024-05-08 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gameplay", "0009_tournament_is_playing_alter_tournament_is_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="tournamentplayer",
            name="is_host",
            field=models.BooleanField(default=False),
        ),
    ]
