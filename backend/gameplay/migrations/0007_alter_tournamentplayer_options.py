# Generated by Django 5.0.1 on 2024-05-06 09:48

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("gameplay", "0006_tournamentplayer_date_added"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="tournamentplayer",
            options={"ordering": ["date_added"]},
        ),
    ]
