# Generated by Django 5.0.1 on 2024-05-02 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gameplay", "0003_remove_gameplayer_loss_remove_gameplayer_win"),
    ]

    operations = [
        migrations.AddField(
            model_name="tournament",
            name="is_finished",
            field=models.BooleanField(default=False),
        ),
    ]
