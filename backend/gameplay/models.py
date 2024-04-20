import random
import string
import uuid
import asyncio

from django.db import models
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

User = get_user_model()


class TournamentPlayer(models.Model):
    player = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    tournament = models.ForeignKey("Tournament", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)


class Tournament(models.Model):
    game_type = models.CharField(max_length=100, default="pong")
    players = models.ManyToManyField("auth.User", through=TournamentPlayer)
    is_active = models.BooleanField(default=False)

    def check_tournament_ready(self):
        if self.players.count() < 3:
            return False
        return True

    def start_tournament(self):
        if not self.check_tournament_ready():
            return False
        self.is_active = True
        self.save()
        return True

    def bracket(self):
        players = self.players.all()
        bracket = []
        for i in range(0, len(players), 2):
            bracket.append([players[i], players[i + 1]])
        return bracket


def generate_game_code():
    return "".join(random.choices(string.ascii_uppercase, k=6))


class GamePlayer(models.Model):
    game_room = models.ForeignKey("GameRoom", on_delete=models.CASCADE)
    player = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=True, default=None
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    is_winner = models.BooleanField(default=False)
    win = models.PositiveIntegerField(default=0)
    loss = models.PositiveIntegerField(default=0)
    score = models.IntegerField(default=0)
    session_id = models.UUIDField(default=uuid.uuid4)
    player_number = models.IntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game_room", "player"], name="Players in room"
            ),
            models.UniqueConstraint(
                fields=["game_room", "player_number"],
                name="Player number unique in room",
            ),
        ]


class GameRoom(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    players = models.ManyToManyField("auth.User", through="GamePlayer")
    is_active = models.BooleanField(default=True)
    is_started = models.BooleanField(default=False)
    is_finished = models.BooleanField(default=False)
    game_code = models.CharField(max_length=10, default=generate_game_code)
    game_type = models.CharField(max_length=100, default="pong")
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True)
    level = models.IntegerField(default=1)
    created_date = models.DateTimeField(auto_now_add=True)
    max_players = models.IntegerField(default=2, blank=True)

    def __str__(self):
        return self.room_name

    class Meta:
        unique_together = ("game_code", "is_active")

    async def add_player_name(self, player_name: str):
        current_player_count = (
            await self.players.acount() if hasattr(self, "players") else 0
        )
        if (
            self.tournament
            or self.is_started
            or current_player_count >= self.max_players
        ):
            return None
        player = await GamePlayer.objects.acreate(
            game_room=self,
            name=player_name,
            is_active=True,
            player_number=current_player_count + 1,
        )
        return player.session_id

    async def add_player(self, player):
        current_player_count = await self.players.acount()
        if self.tournament and await self.players.filter(player=player).aexists():
            game_player = await GamePlayer.objects.get(player=player, game_room=self)
            game_player.is_active = True
            game_player.save()
            return
        if (
            self.tournament
            or self.is_started
            or current_player_count >= self.max_players
        ):
            return
        game_player = await GamePlayer.objects.acreate(
            game_room=self,
            player=player,
            name=player.username,
            player_number=current_player_count + 1,
            is_active=True,
        )
        return game_player.session_id

    async def get_players(self):
        players = [
            {
                "name": player.name,
                "player_id": player.session_id,
            }
            async for player in GamePlayer.objects.filter(
                game_room=self, is_active=True
            ).order_by("player_number")
        ]
        return players

    async def set_inactive(self):
        self.is_active = False
        await self.asave()

    async def update_win_loss(self, game_room):
        async for gp_obj in GamePlayer.objects.filter(game_room=game_room).select_related('player'):
            # player_username = gp_obj.player.username if gp_obj.player else 'Anonymous'
            # print(f"Player username: {player_username}")
            # print(f"In for loop to update win, loss, is_win: {gp_obj.is_winner}")
            if gp_obj.is_winner is True:
                gp_obj.win += 1
            else:
                gp_obj.loss += 1
            await gp_obj.asave()

    async def force_end(self, player_id):
        # print("In force_end")
        if not player_id:
            print("Invalid player_id")
            return
        self.is_active = False
        self.is_finished = True
        # print(f"player_id: {player_id}")
        await (
            GamePlayer.objects.filter(game_room=self)
            .exclude(session_id=player_id)
            .aupdate(is_winner=True)
        )
        await self.asave()

        test_obj = await sync_to_async(GamePlayer.objects.filter(game_room=self).count)()
        if test_obj <= 1:
            return
        await self.update_win_loss(self)

    async def victory(self, player_id):
        self.is_active = False
        self.is_finished = True
        await (
            GamePlayer.objects.filter(game_room=self)
            .filter(session_id=player_id)
            .aupdate(is_winner=True)
        )
        await self.asave()

    async def test_user_record(self, user, player_id):
        print("In test_user_record")
        await self.force_end(player_id)
        print("after force_end")
        win = 0
        loss = 0

        async for gp_obj in GamePlayer.objects.filter(player=user):
            print(f"In for loop to update win, loss, is_win: {gp_obj.is_winner}")
            win += gp_obj.win
            loss += gp_obj.loss
            await gp_obj.asave()

        print(f"username: {user.username}, win: {win}, loss: {loss}")

    def get_player_by_num(self, player_number) -> GamePlayer:
        return GamePlayer.objects.filter(
            game_room=self, player_number=player_number
        ).first()

    def get_scores(self) -> str:
        score_str = ""
        players = (
            GamePlayer.objects.filter(game_room=self, is_active=True)
            .order_by("player_number")
            .all()
        )
        for i in range(self.max_players):
            if score_str:
                score_str += " - "
            if i >= len(players):
                score_str += "0"
                continue
            score_str += str(players[i].score)
        return score_str

    def is_winner(self, user):
        return (
            GamePlayer.objects.filter(game_room=self, is_active=True)
            .filter(player=user, is_winner=True)
            .exists()
        )

# class UserRecord(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     game_room = models.ForeignKey("GameRoom", on_delete=models.CASCADE, null=True, default=None)
#     player_id = models.UUIDField(default=uuid.uuid4)
#     win = models.PositiveIntegerField(default=0)
#     loss = models.PositiveIntegerField(default=0)

#     @classmethod
#     @sync_to_async
#     def record_result(cls, user, is_winner):
#         user_record, _ = cls.objects.get_or_create(user)
#         if is_winner:
#             user_record.win += 1
#         else:
#             user_record.loss += 1
#         user_record.save()

#     @classmethod
#     @sync_to_async
#     def create_user_record(cls, user, game_room, player_id):
#         user_record,_ = cls.objects.get_or_create(user=user, game_room=game_room, player_id=player_id)
#         return user_record

#     @classmethod
#     async def test_user_record(cls, user, game_room, player_id):
#         await game_room.force_end(player_id)
#         user_records_queryset = await sync_to_async(UserRecord.objects.filter)(user=user)
#         # user = user_records_queryset.select_related('user')
#         user_records = await sync_to_async(list)(user_records_queryset)
#         win = 0
#         loss = 0
#         for obj in user_records:
#             win += obj.win
#             loss += obj.loss
#         print(f"username: {user.username}, win: {win}, loss: {loss}")

#         print("Dummy")
#         game_player_queryset = await sync_to_async(GamePlayer.objects.filter)(player=user)
#         game_player_queryset = game_player_queryset.select_related('player')
#         game_players = await sync_to_async(list)(game_player_queryset)
#         win = 0
#         loss = 0
#         for obj in game_players:
#             if obj.player == user:
#                 print("player == user")
#                 if obj.is_winner is True:
#                     win += 1
#                 elif obj.is_winner is False:
#                     loss += 1
#         print(f"user: {user.username}, win: {win}, loss: {loss}")

# class PlayerUserMap(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     playerName = models.TextField()
#     channel_name = models.TextField(null=True)

#     @classmethod
#     @sync_to_async
#     def get_username(cls, playerName):
#         try:
#             map = cls.objects.get(playerName=playerName)
#             return map.user.username
#         except cls.DoesNotExist:
#             return None

#     @classmethod
#     @sync_to_async
#     def get_channel_name(cls, playerName):
#         try:
#             obj = cls.objects.get(playerName=playerName)
#             return obj.channel_name
#         except cls.DoesNotExist:
#             return None

#     @classmethod
#     @sync_to_async
#     def update_channel_name(cls, playerName, channel_name):
#         try:
#             player_user_map = cls.objects.get(playerName=playerName)
#             player_user_map.channel_name = channel_name
#             player_user_map.save()
#         except cls.DoesNotExist:
#             pass
