from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model
# from django.utils import timezone
from django.contrib.postgres.fields import ArrayField

# Create your models here.
User = get_user_model()

class Chat(models.Model):
	# hold the reference to the user who authored the message
	#ForeignKey is a field type in Django used to define many-to-one relationships https://docs.djangoproject.com/en/5.0/topics/db/examples/many_to_one/
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
	content = models.TextField()
	timestamp = models.DateTimeField(auto_now_add=True)

#Each Chat instance is associated with exactly one ChatRoom instance
class ChatRoom(models.Model):
	name = models.TextField()

class BlockUser(models.Model):
	own_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, default=None)
	own_name = models.TextField()
	blocked_players = ArrayField(models.TextField(), default=list)

	def block_user(self, blocked_playerName):
		if blocked_playerName not in self.blocked_players:
			self.blocked_players.append(blocked_playerName)
			self.save()
			return True
		return False

	def unblock_user(self, blocked_playerName):
		if blocked_playerName in self.blocked_players:
			self.blocked_players.remove(blocked_playerName)
			self.save()
			return True
		return False

	def is_blocked_user(self, blocked_playerName):
		# Filter Chat instances associated with the user and have sender equal to playerName
		return blocked_playerName in self.blocked_players
