# Generated by Django 5.0.1 on 2024-05-06 14:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0015_memberchatroom_delete_userlist"),
    ]

    operations = [
        migrations.DeleteModel(
            name="MemberChatRoom",
        ),
    ]
