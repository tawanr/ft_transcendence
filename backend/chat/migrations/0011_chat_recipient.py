# Generated by Django 5.0.1 on 2024-04-24 11:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0010_chat_notification"),
    ]

    operations = [
        migrations.AddField(
            model_name="chat",
            name="recipient",
            field=models.TextField(default=None),
        ),
    ]
