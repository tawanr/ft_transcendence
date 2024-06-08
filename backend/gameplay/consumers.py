import asyncio
import json
import logging

from account.models import UserToken
from channels.generic.websocket import AsyncWebsocketConsumer
from django.http import JsonResponse

import gameplay.constants as constants
from gameplay.models import GamePlayer, GameRoom
from gameplay.states import BallState, GameState, PlayerState

logger = logging.getLogger(__name__)


class GameplayConsumer(AsyncWebsocketConsumer):
    game_group_name: str = "game_group"
    host: bool = False
    game: GameState = GameState()
    player_id: str = ""
    registered = False

    update_lock = asyncio.Lock()

    async def connect(self):
        game_code = self.scope["url_route"]["kwargs"].get("room_name")
        await self.accept()

        if game_code:
            game_room = await GameRoom.objects.filter(
                game_code=game_code, is_active=True
            ).afirst()

        if not game_code or not game_room:
            logger.info("Creating new game room.")
            game_room = await GameRoom.objects.acreate()

        await self.game.reset_states()

        self.game.room = game_room
        self.game_code = game_room.game_code
        self.game_group_name = f"game_{self.game_code}"

        asyncio.create_task(self.check_registered())

    async def check_registered(self):
        await asyncio.sleep(2)
        async with self.update_lock:
            if not self.registered:
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "disconnect",
                            "details": "No player registered. Closing connection.",
                        }
                    )
                )
                await self.close()
                return

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                "type": "player.leave",
                "player_id": self.player_id,
            },
        )

        if self.host:
            await self.game.room.set_inactive()
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)

    async def set_players(self):
        players = await self.game.room.get_players()
        for idx, player in enumerate(players):
            self.game.players[idx].player_id = player["player_id"]
            self.game.players[idx].player_name = player["name"]
        if self.game.players[0].player_id == self.player_id:
            self.host = True

    async def receive(self, text_data):
        print("Gameplay in receive function")
        data = json.loads(text_data)

        try:
            if data["type"] == "client.register":
                token = None
                if authorization := data.get("authorization"):
                    token = (
                        await UserToken.objects.filter(access_token=authorization)
                        .select_related("user")
                        .afirst()
                    )
                    if not token or not token.is_token_valid():
                        return JsonResponse({"details": "Unauthorized"}, status=401)
                    if player := await GamePlayer.objects.filter(
                        game_room=self.game.room, player=token.user
                    ).afirst():
                        self.player_id = player.session_id
                    else:
                        self.player_id = await self.game.room.add_player(token.user)
                elif name := data.get("playerName"):
                    self.player_id = await self.game.room.add_player_name(name)
                else:
                    await self.send(
                        text_data={
                            "type": "disconnect",
                            "details": "Invalid registration. Closing connection.",
                        }
                    )
                    await self.close()
                    return
                self.registered = True
                await self.set_players()

                await self.channel_layer.group_add(
                    self.game_group_name,
                    self.channel_name,
                )
                print("Before send function")
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "roomDetails",
                            "roomCode": self.game_code,
                            "playerId": str(self.player_id),
                            "player_user": token.user.username if token else "",
                        }
                    )
                )

                await self.update_group()
                await self.send_group()
        except Exception as e:
            logger.error(f"Error: {e}")

        if not self.player_id:
            return

        message = {
            **data,
            "player_id": self.player_id,
        }
        print("Before group send")
        await self.channel_layer.group_send(
            self.game_group_name,
            message,
        )

    async def client_register(self, event):
        pass

    async def player_leave(self, event):
        self.game.started = False
        if not self.host:
            return
        await self.game.ball.reset_pos()
        await self.game.room.force_end(event["player_id"])
        for player in self.game.players:
            player.ready = False
        logger.info(f"\nPlayer Disconnected: {event['player_id']}\n")
        await self.update_group()
        await self.end_game(self.player_id)

    async def player_ready(self, event):
        if not self.host or self.game.started:
            return
        player = await self.game.get_player(event["id"])
        await player.set_ready()
        await self.update_group()
        for player in self.game.players:
            if not player.ready:
                return
        # print("Player ready!!!!!!")
        await self.game.start()
        asyncio.create_task(self.game_loop())

    async def player_controls(self, event):
        if not self.host:
            return
        player = await self.game.get_player(event["id"])
        if not player:
            return
        await player.set_controls(event["up"], event["down"])
        await self.update_group()

    async def state_update(self, event):
        if "players" in event:
            self.game.players = event["players"]
        if "game" in event:
            self.game = event["game"]
        if "ball" in event:
            self.game.ball = event["ball"]

    async def state_send(self, event):
        data = {
            "type": "gameState",
        }
        for player in self.game.players:
            selector = "player1"
            score = self.game.ball.score_1
            if not player.player1:
                selector = "player2"
                score = self.game.ball.score_2
            data[selector] = {
                "x": player.x,
                "y": player.y,
                "score": score,
                "name": player.player_name,
                "ready": player.ready,
            }
        data["ball"] = {
            "x": self.game.ball.x,
            "y": self.game.ball.y,
        }
        await self.send(text_data=json.dumps(data))

    async def send_group(self):
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                "type": "state.send",
            },
        )

    async def update_group(self):
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                "type": "state.update",
                "players": self.game.players,
                "game": self.game,
                "ball": self.game.ball,
            },
        )

    async def end_game(self, player_id):
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                "type": "state.end",
                "winner_id": str(player_id),
            },
        )

    async def state_end(self, event):
        msg = {
            "type": "gameEnd",
            "winnerId": event["winner_id"],
        }
        await self.send(text_data=json.dumps(msg))

    async def game_loop(self):
        if not self.host:
            return
        logger.debug("\nGame started.\n")
        await self.game.ball.reset_pos()
        while self.game.started:
            try:
                async with self.update_lock:
                    for player in self.game.players:
                        await player.update()
                    await self.game.ball.update(self.game.players)
                if player_id := await self.game.update():
                    print(f"Winner: {player_id}")
                    await self.end_game(player_id)
                await self.update_group()
                await self.send_group()
                await asyncio.sleep(0.03)
            except Exception as e:
                logger.error(f"Game loop error: {e}")
                self.game.started = False
        logger.debug("\nGame ended.\n")
