import asyncio
import random
import string
import uuid

from asgiref.sync import sync_to_async
from chat.models import User
from django.contrib.auth import get_user_model
from django.db import models


class RoundNotFinishedException(Exception):
    pass


class TournamentPlayer(models.Model):
    player = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    tournament = models.ForeignKey("Tournament", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_winner = models.BooleanField(default=False)
    is_host = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ["date_added"]


class Tournament(models.Model):
    game_type = models.CharField(max_length=100, default="pong")
    players = models.ManyToManyField("auth.User", through=TournamentPlayer)
    is_active = models.BooleanField(default=True)
    is_playing = models.BooleanField(default=False)
    is_finished = models.BooleanField(default=False)
    size = models.IntegerField(default=4)

    async def set_host(self, user: User):
        if not user:
            if not self.players.through.objects.filter(
                is_host=True, tournament=self
            ).aexists():
                user = await self.players.afirst()
            else:
                return
        if not user:
            return
        await self.players.through.objects.filter(tournament=self).aupdate(
            is_host=False
        )
        if not await self.players.through.objects.filter(player=user).aexists():
            await self.add_player(user, is_host=True)
        else:
            await self.players.through.objects.filter(
                player=user, tournament=self
            ).aupdate(is_host=True)

    async def get_host(self) -> User:
        host = (
            await self.players.through.objects.filter(tournament=self, is_host=True)
            .select_related("player")
            .afirst()
        )
        return host.player

    async def add_player(self, player, is_host=False):
        from account.models import UserNotifications
        await sync_to_async(self.players.add)(player)
        # await UserNotifications.objects.acreate(
        #     user=player,
        #     type="tour_invite",
        #     referral=self.id,
        # )
        if await self.players.acount() > self.size:
            self.size *= 2
            await self.asave()
        if tour_player := await self.players.through.objects.filter(
            player=player,
            tournament=self,
        ).afirst():
            if is_host or await self.players.acount() == 1:
                tour_player.is_host = True
                await tour_player.asave()
            return tour_player

    @property
    async def is_ready(self):
        if self.is_finished or await self.players.acount() < 3:
            return False
        return True

    async def get_winner(self):
        if not self.is_finished:
            return None
        winner = (
            await self.players.through.objects.filter(tournament=self, is_winner=True)
            .select_related("player")
            .afirst()
        )
        return winner.player

    async def start_tournament(self):
        if not await self.is_ready:
            return False
        # Check if there are existing games
        self.is_playing = True
        await self.asave()
        await self._create_round_games(level=1)
        return True

    async def _create_round_games(self, level):
        from account.models import UserNotifications
        games = []
        round_size = int(self.size / (level * 2))
        players = [
            player.player
            async for player in self.players.through.objects.filter(
                is_active=True,
                tournament=self,
            ).select_related("player")
        ]
        for idx, player in enumerate(players):
            if idx < round_size:
                games.append(
                    await GameRoom.objects.acreate(tournament=self, level=level)
                )
            await games[idx % round_size].add_player(player)
            await UserNotifications.objects.acreate(
                user=player,
                type="game_start",
                referral=self.id,
            )
        for game in games:
            if await game.players.acount() == 1:
                await game.victory(
                    (await GamePlayer.objects.aget(game_room=game)).session_id
                )
                await game.asave()

    async def bracket(self):
        games = await self.get_games()
        size = self.size / 2
        total = size
        while size > 1:
            size /= 2
            total += size
        bracket = []
        for game in games:
            players = [
                player
                async for player in game.gameplayer_set.values(
                    "name", "score", "is_winner", "player__id"
                )
            ]
            game_bracket = {
                "finished": game.is_finished,
                "players": [
                    {
                        "id": player["player__id"],
                        "name": player["name"],
                        "score": player["score"],
                        "isWinner": player["is_winner"],
                    }
                    for player in players
                ],
            }
            if len(game_bracket.get("players")) < 2:
                game_bracket["players"].append({})
            bracket.append(game_bracket)
        while len(bracket) < total:
            bracket.append({})
        return bracket

    async def get_games(self, level=None, is_active=False):
        qs = GameRoom.objects.filter(
            tournament=self,
        ).order_by("created_date")
        if is_active:
            qs = qs.filter(is_active=is_active)
        if level:
            qs = qs.filter(level=level)
        return [game async for game in qs]

    async def get_players(self) -> dict:
        players = []
        async for player in self.players.select_related("details").all():
            players.append(await sync_to_async(player.details.serialize)())
        return players

    async def check_round_end(self) -> bool:
        qs_games = GameRoom.objects.filter(tournament=self, is_finished=False)
        if await qs_games.aexists():
            return False
        return True

    async def start_new_round(self) -> bool:
        if not await self.check_round_end():
            raise RoundNotFinishedException("Round not finished")
        current_round = await self.get_current_round()
        if (
            await self.players.through.objects.filter(
                is_active=True,
                tournament=self,
            ).acount()
            == 1
        ):
            await self.players.through.objects.filter(
                is_active=True,
                tournament=self,
            ).aupdate(is_winner=True)
            self.is_finished = True
            self.is_active = False
            await self.asave()
            return False
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
        current_player_count = await GamePlayer.objects.filter(
            game_room=self, is_active=True
        ).acount()
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
            async for player in GamePlayer.objects.filter(game_room=self).order_by(
                "player_number"
            )
        ]
        return players

    async def set_inactive(self):
        self.is_active = False
        await self.asave()

    async def end_game(self):
        self.is_active = False
        self.is_finished = True
        await self.asave()
        async for player in GamePlayer.objects.filter(game_room=self):
            player.is_active = False
            await player.asave()
        await self.check_tournament()

    async def check_tournament(self):
        tournament = await Tournament.objects.filter(gameroom=self).afirst()
        if not tournament:
            return
        try:
            await tournament.start_new_round()
        except RoundNotFinishedException:
            pass

    async def force_end(self, player_id):
        if not player_id:
            return
        winner = await self.players.exclude(gameplayer__session_id=player_id).afirst()
        await self.players.through.objects.filter(
            player=winner, game_room=self
        ).aupdate(is_winner=True)
        await self._deactivate_tournament_player(
            await self.players.exclude(id=winner.id).afirst()
        )
        await self.end_game()

    async def victory(self, player_id):
        winner = (
            await GamePlayer.objects.filter(session_id=player_id)
            .select_related("game_room", "game_room__tournament", "player")
            .afirst()
        )
        if not winner:
            raise Exception("Player not found")
        winner.is_winner = True
        await winner.asave()
        if winner.game_room.tournament:
            await self._deactivate_tournament_player(
                await self.players.exclude(id=winner.player.id).afirst()
            )
        await self.end_game()

    async def _deactivate_tournament_player(self, user: User):
        if not user:
            return
        tournament = await Tournament.objects.aget(gameroom=self)
        if not tournament:
            return
        await tournament.players.through.objects.filter(
            player=user, tournament=tournament
        ).aupdate(is_active=False)

    def get_player_by_num(self, player_number) -> GamePlayer:
        return GamePlayer.objects.filter(
            game_room=self, player_number=player_number
        ).first()

    def get_scores(self) -> str:
        score_str = ""
        players = (
            GamePlayer.objects.filter(game_room=self).order_by("player_number").all()
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
            GamePlayer.objects.filter(game_room=self)
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
