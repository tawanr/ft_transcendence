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


class GamePlayer(models.Model):
    game_room = models.ForeignKey("GameRoom", on_delete=models.CASCADE)
    player = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=True, default=None
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    is_winner = models.BooleanField(default=False)
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

    async def force_end(self, player_id):
        self.is_active = False
        self.is_finished = True
        await (
            GamePlayer.objects.filter(game_room=self)
            .exclude(session_id=player_id)
            .aupdate(is_winner=True)
        )
        await self.asave()

    async def victory(self, player_id):
        self.is_active = False
        self.is_finished = True
        await (
            GamePlayer.objects.filter(game_room=self)
            .filter(session_id=player_id)
            .aupdate(is_winner=True)
        )
        await self.asave()

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
