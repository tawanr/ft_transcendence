# Generated by Django 5.0.1 on 2024-05-09 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0002_userdetails_userfriendinvite"),
    ]

    operations = [
        migrations.AddField(
            model_name="userdetails",
            name="is_connected",
            field=models.BooleanField(default=False),
        ),
    ]
