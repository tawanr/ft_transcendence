import json
import asyncio
import gameplay.constants as constants
from typing import Dict

from uuid import uuid4
from channels.generic.websocket import AsyncWebsocketConsumer
from gameplay.states import PlayerState, BallState, GameState


class GameplayConsumer(AsyncWebsocketConsumer):
    game_group_name: str = "game_group"
    players: Dict[str, PlayerState] = {}
    host: bool = False
    game_state: GameState = GameState()
    ball_state: BallState = BallState(
        x=(constants.GAME_WIDTH / 2) - (constants.BALL_SIZE / 2),
        y=(constants.GAME_HEIGHT / 2) - (constants.BALL_SIZE / 2),
        width=constants.BALL_SIZE,
        height=constants.BALL_SIZE,
    )
    player_id: str = ""

    update_lock = asyncio.Lock()

    async def connect(self):
        self.player_id = str(uuid4())
        self.game_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.game_group_name = f"game_{self.game_name}"
        await self.accept()

        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name,
        )

        await self.channel_layer.group_send(
            self.game_group_name,
            {
                "type": "player.join",
                "player_id": self.player_id,
            },
        )

        await self.send(
            text_data=json.dumps(
                {
                    "type": "playerId",
                    "playerId": self.player_id,
                    "roomId": self.game_name,
                }
            )
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                "type": "player.leave",
                "player_id": self.player_id,
            },
        )
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.game_group_name,
            data,
        )

    async def player_leave(self, event):
        self.players.pop(event["player_id"])
        if not self.host:
            return
        for player in self.players.values():
            player.ready = False
        self.game_state.started = False
        print(f"\nPlayer Disconnected: {event['player_id']}\n")
        await self.update_group()

    async def player_join(self, event):
        if event["player_id"] in self.players:
            return
        player_id = event["player_id"]
        new_player = PlayerState(
            player_id=player_id,
            x=constants.PLAYER_LEFT_OFFSET,
            y=(self.game_state.height / 2) - (constants.PLAYER_HEIGHT / 2),
            speed=constants.PLAYER_SPEED,
            width=constants.PLAYER_WIDTH,
            height=constants.PLAYER_HEIGHT,
        )
        if len(self.players) > 0:
            new_player.player1 = False
            new_player.x = (
                constants.GAME_WIDTH - constants.PLAYER_RIGHT_OFFSET - new_player.width
            )
        self.players[player_id] = new_player
        print(f"\nPlayer Joined: {player_id}\n")
        if len(self.players) == 2:
            self.host = True
            print(f"\n{self.player_id} is the host.\n")
        self.send_group()

    async def player_ready(self, event):
        if not self.host or self.game_state.started:
            return
        player = self.players.get(event["id"])
        player.ready = True
        self.players[event["id"]] = player
        await self.update_group()
        for player in self.players.values():
            if not player.ready:
                return
        self.game_state.started = True
        asyncio.create_task(self.game_loop())

    async def player_controls(self, event):
        if not self.host:
            return
        player = self.players.get(event["id"])
        if not player:
            return
        player.up_key = event["up"]
        player.down_key = event["down"]
        self.players[event["id"]] = player
        await self.update_group()

    async def state_update(self, event):
        if "players" in event:
            self.players = event["players"]
        if "game" in event:
            self.game_state = event["game"]
        if "ball" in event:
            self.ball_state = event["ball"]

    async def state_send(self, event):
        data = {
            "type": "gameState",
        }
        for player in self.players.values():
            selector = "player1"
            score = self.ball_state.score_1
            if not player.player1:
                selector = "player2"
                score = self.ball_state.score_2
            data[selector] = {
                "x": player.x,
                "y": player.y,
                "score": score,
                "name": player.player_name,
                "ready": player.ready,
            }
        data["ball"] = {
            "x": self.ball_state.x,
            "y": self.ball_state.y,
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
                "players": self.players,
                "game": self.game_state,
                "ball": self.ball_state,
            },
        )

    async def game_loop(self):
        if not self.host:
            return
        print("\nGame started.\n")
        await self.ball_state.reset_pos()
        while len(self.players) == 2 and self.game_state.started:
            async with self.update_lock:
                for player in self.players.values():
                    await player.update()
                await self.ball_state.update(self.players.values())
            await self.update_group()
            await self.send_group()
            await asyncio.sleep(0.03)
        print("\nGame ended.\n")
