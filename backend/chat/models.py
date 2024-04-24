from django.db import models
from django.db.models import Max

# Create your models here.
from django.contrib.auth import get_user_model
# from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from asgiref.sync import sync_to_async

# Create your models here.
User = get_user_model()

class Chat(models.Model):
	# hold the reference to the user who authored the message
	#ForeignKey is a field type in Django used to
	# define many-to-one relationships https://docs.djangoproject.com/en/5.0/topics/db/examples/many_to_one/
	#User => model with which the foreign key relationship is established
	#related_name='author_message => defines the reverse relationship from the User model back to the Message mode
	#allows you to access messages authored by a specific user
	#specifies the behavior to adopt when the referenced object is deleted
	#CASCADE => If a User instance is deleted, all associated Chat instances will also be deleted
	#If you don't specify related_name in ForeignKey(), when you access related obj you have to use default relate name "_set"
	#Ex. You have Message instance called "message" you can access related User instance by "message.user_set"
	user = models.ForeignKey(User, on_delete=models.CASCADE) #user is player name not username
	room = models.ForeignKey('ChatRoom', on_delete=models.CASCADE)
	sender = models.TextField()
	recipient = models.TextField(default=None)
	content = models.TextField()
	timestamp = models.DateTimeField(auto_now_add=True)
	notification = models.BooleanField(default=False)

	async def assign_notification(self, status, sender):
		print("In assign_noti")
		# latest_timestamp = Chat.objects.aggregate(latest_timestamp=Max('timestamp'))['latest_timestamp']
		latest_timestamp_dict = await sync_to_async(Chat.objects.aggregate)(latest_timestamp=Max('timestamp'))
		latest_timestamp = latest_timestamp_dict['latest_timestamp']

		async for ch_obj in Chat.objects.filter(sender=sender, timestamp=latest_timestamp):
			print(f"sender: {ch_obj.sender}")
			print(f"content: {ch_obj.content}")
			print(f"timestamp: {ch_obj.timestamp}")
			print(f"{ch_obj.timestamp}, status: {status}")
			ch_obj.notification = status
			await ch_obj.asave()

#Each Chat instance is associated with exactly one ChatRoom instance
class ChatRoom(models.Model):
	name = models.TextField()

class BlockUser(models.Model):
	own_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, default=None)
	own_username = models.TextField()
	blocked_users = ArrayField(models.TextField(), default=list)

	def block_user(self, blocked_username):
		if blocked_username not in self.blocked_users:
			self.blocked_users.append(blocked_username)
			self.save()
			return True
		return False

	def unblock_user(self, blocked_username):
		if blocked_username in self.blocked_users:
			self.blocked_users.remove(blocked_username)
			self.save()
			return True
		return False

	def is_blocked_user(self, blocked_username):
		# Filter Chat instances associated with the user and have sender equal to playerName
		return blocked_username in self.blocked_users
