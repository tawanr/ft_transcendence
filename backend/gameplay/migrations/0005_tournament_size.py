# Generated by Django 5.0.1 on 2024-05-06 06:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gameplay", "0004_tournament_is_finished"),
    ]

    operations = [
        migrations.AddField(
            model_name="tournament",
            name="size",
            field=models.IntegerField(default=4),
        ),
    ]
