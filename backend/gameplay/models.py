import asyncio
import random
import string
import uuid

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import models

from chat.models import User


class TournamentPlayer(models.Model):
    player = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    tournament = models.ForeignKey("Tournament", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_winner = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ["date_added"]


class Tournament(models.Model):
    game_type = models.CharField(max_length=100, default="pong")
    players = models.ManyToManyField("auth.User", through=TournamentPlayer)
    is_active = models.BooleanField(default=False)
    is_finished = models.BooleanField(default=False)
    size = models.IntegerField(default=4)

    async def add_player(self, player):
        await sync_to_async(self.players.add)(player)
        if await self.players.acount() > self.size:
            self.size *= 2
            await self.asave()

    @property
    async def is_ready(self):
        if self.is_finished or await self.players.acount() < 3:
            return False
        return True

    async def start_tournament(self):
        if not await self.is_ready:
            return False
        # Check if there are existing games
        self.is_active = True
        await self.asave()
        await self._create_round_games(level=1)
        return True

    async def _create_round_games(self, level):
        games = []
        round_size = int(self.size / (level * 2))
        players = [
            player.player
            async for player in self.players.through.objects.filter(
                is_active=True
            ).select_related("player")
        ]
        for idx, player in enumerate(players):
            if idx < round_size:
                games.append(
                    await GameRoom.objects.acreate(tournament=self, level=level)
                )
            await games[idx % round_size].add_player(player)
        for game in games:
            if await game.players.acount() == 1:
                await game.victory(
                    (await GamePlayer.objects.aget(game_room=game)).session_id
                )
                await game.asave()

    async def bracket(self):
        players = self.players.all()
        bracket = []
        for i in range(0, len(players), 2):
            bracket.append([players[i], players[i + 1]])
        return bracket

    async def get_games(self, level=None, is_active=False):
        qs = GameRoom.objects.filter(
            tournament=self,
        )
        if is_active:
            qs = qs.filter(is_active=is_active)
        if level:
            qs = qs.filter(level=level)
        return [game async for game in qs]

    async def check_round_end(self) -> bool:
        qs_games = GameRoom.objects.filter(tournament=self, is_finished=False)
        if await qs_games.aexists():
            return False
        return True

    async def start_new_round(self) -> bool:
        if not await self.check_round_end():
            return False
        current_round = await self.get_current_round()
        if await self.players.through.objects.filter(is_active=True).acount() == 1:
            await self.players.through.objects.filter(is_active=True).aupdate(
                is_winner=True
            )
            self.is_finished = True
            self.is_active = False
            await self.asave()
        await self._create_round_games(current_round + 1)
        return True

    async def get_current_round(self) -> int:
        level = (
            await GameRoom.objects.filter(tournament=self)
            .order_by("-level")
            .values_list("level", flat=True)
            .distinct()
            .afirst()
        )
        return level if level > 0 else 0


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
    # win = models.PositiveIntegerField(default=0)
    # loss = models.PositiveIntegerField(default=0)
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

    # async def get_win(self, user):
    #     win = 0
    #     async for gp_obj in GamePlayer.objects.filter(player=user):
    #         win += gp_obj.win
    #     return win

    # async def get_loss(self, user):
    #     loss = 0
    #     async for gp_obj in GamePlayer.objects.filter(player=user):
    #         loss += gp_obj.loss
    #     return loss


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
        return self.game_code

    class Meta:
        unique_together = ("game_code", "is_active")

    async def add_player_name(self, player_name: str):
        current_player_count = (
            await GamePlayer.objects.filter(game_room=self).acount()
            if hasattr(self, "players")
            else 0
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
        # if self.tournament and await self.players.filter(player=player).aexists():
        #     game_player = await GamePlayer.objects.aget(player=player, game_room=self)
        #     game_player.is_active = True
        #     game_player.save()
        #     return
        # if (
        #     self.tournament
        #     or self.is_started
        #     or current_player_count >= self.max_players
        # ):
        #     return
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

    # async def update_win_loss(self, game_room):
    #     async for gp_obj in GamePlayer.objects.filter(game_room=game_room).select_related('player'):
    #         if gp_obj.is_winner is True:
    #             gp_obj.win += 1
    #         else:
    #             gp_obj.loss += 1
    #         await gp_obj.asave()

    async def force_end(self, player_id):
        if not player_id:
            return
        self.is_active = False
        self.is_finished = True
        winner = await self.players.exclude(gameplayer__session_id=player_id).afirst()
        await self.players.through.objects.filter(player=winner).aupdate(is_winner=True)
        await self._deactivate_tournament_player(
            await self.players.exclude(id=winner.id).afirst()
        )
        await self.asave()

        # test_obj = await sync_to_async(GamePlayer.objects.filter(game_room=self).count)()
        # if test_obj <= 1:
        #     return
        # await self.update_win_loss(self)

    async def victory(self, player_id):
        self.is_active = False
        self.is_finished = True
        winner = await self.players.filter(gameplayer__session_id=player_id).afirst()
        await self.players.through.objects.filter(player=winner).aupdate(is_winner=True)
        await self._deactivate_tournament_player(
            await self.players.exclude(id=winner.id).afirst()
        )
        await self.asave()
        # await self.update_win_loss(self)

    async def _deactivate_tournament_player(self, user: User):
        if not user:
            return
        tournament = await Tournament.objects.aget(gameroom=self)
        if not tournament:
            return
        await tournament.players.through.objects.filter(player=user).aupdate(
            is_active=False
        )

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

    @property
    def host(self):
        host = GamePlayer.objects.filter(game_room=self).first()
        return host

    async def test_user_record(self, user, player_id):
        await self.victory(player_id)
        # win = 0
        # loss = 0

        async for gp_obj in GamePlayer.objects.filter(player=user):
            # print(f"In for loop to update win, loss, is_win: {gp_obj.is_winner}")
            # win += gp_obj.win
            # loss += gp_obj.loss
            await gp_obj.asave()

        # print(f"username: {user.username}, win: {win}, loss: {loss}")
