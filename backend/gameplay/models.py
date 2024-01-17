import random
import string
import uuid

from django.db import models


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


class GameRoom(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    players = models.ManyToManyField("auth.User")
    player1_name = models.CharField(max_length=100, default="")
    player2_name = models.CharField(max_length=100, default="")
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    player1_session_id = models.UUIDField(null=True)
    player2_session_id = models.UUIDField(null=True)
    is_active = models.BooleanField(default=True)
    is_started = models.BooleanField(default=False)
    is_finished = models.BooleanField(default=False)
    player1_won = models.BooleanField(default=False)
    game_code = models.CharField(max_length=10, default=generate_game_code)
    game_type = models.CharField(max_length=100, default="pong")
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True)
    level = models.IntegerField(default=1)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.room_name

    class Meta:
        unique_together = ("game_code", "is_active")

    async def add_player_name(self, player_name: str):
        if self.tournament or self.is_started:
            return None
        if not self.player1_name:
            self.player1_name = player_name
            self.player1_session_id = uuid.uuid4()
            await self.asave()
            return self.player1_session_id
        elif not self.player2_name:
            self.player2_name = player_name
            self.player2_session_id = uuid.uuid4()
            await self.asave()
            return self.player2_session_id
        return None

    async def add_player(self, player):
        if self.tournament or self.is_started:
            if not self.players.filter(id=player.id).exists():
                return None
            if self.player1_name == player.username:
                self.player1_session_id = uuid.uuid4()
                await self.asave()
                return self.player1_session_id
            if self.player2_name == player.username:
                self.player2_session_id = uuid.uuid4()
                await self.asave()
                return self.player2_session_id
        current_count = await self.players.acount()
        if not current_count < 2:
            return None
        await self.players.aadd(player)
        if current_count == 0:
            self.player1_name = player.username
            self.player1_session_id = uuid.uuid4()
            await self.asave()
            return self.player1_session_id
        if current_count == 1:
            self.player2_name = player.username
            self.player2_session_id = uuid.uuid4()
            await self.asave()
            return self.player2_session_id

    async def get_players(self):
        return [
            {
                "name": self.player1_name,
                "player_id": self.player1_session_id,
            },
            {
                "name": self.player2_name,
                "player_id": self.player2_session_id,
            },
        ]

    async def set_inactive(self):
        self.is_active = False
        await self.asave()

    async def force_end(self, player_id):
        self.is_active = False
        self.is_finished = True
        if self.player2_session_id == player_id:
            self.player1_won = True
        await self.asave()

    async def victory(self, player_id):
        self.is_active = False
        self.is_finished = True
        if self.player1_session_id == player_id:
            self.player1_won = True
        await self.asave()
