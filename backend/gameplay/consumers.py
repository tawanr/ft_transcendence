import json
import math
import asyncio
from random import randrange
import gameplay.constants as constants
from typing import Dict, List

from uuid import uuid4
from attr import dataclass
from channels.generic.websocket import AsyncWebsocketConsumer


@dataclass
class EntityState:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    speed: int = 0


@dataclass
class PlayerState(EntityState):
    player_id: str = ""
    player1: bool = True
    player_name: str = "Player"
    score: int = 0
    ready: bool = False
    up_key: bool = False
    down_key: bool = False

    async def update(self):
        if self.up_key:
            self.y -= self.speed
        if self.down_key:
            self.y += self.speed
        if self.y + self.height > constants.GAME_HEIGHT:
            self.y = constants.GAME_HEIGHT - self.height
        elif self.y < 0:
            self.y = 0


@dataclass
class BallState(EntityState):
    direction: int = 0
    score_1: int = 0
    score_2: int = 0

    async def update(self, players: List[PlayerState]):
        diff_x = self.speed * math.cos(math.radians(self.direction))
        diff_y = self.speed * math.sin(math.radians(self.direction))
        self.x += diff_x
        self.y += diff_y
        for player in players:
            await self.check_collision(player)
        if self.x <= 0:
            self.score_1 += 1
            await self.reset_pos()
        elif self.x + self.width >= constants.GAME_WIDTH:
            self.score_2 += 1
            await self.reset_pos()

    async def check_collision(self, player: PlayerState):
        if player.player1:
            if (
                self.x < player.x + player.width
                and self.x > player.x
                and self.y > player.y
                and self.y < player.y + player.height
            ):
                self.direction = 180 - self.direction
                self.speed += 0.2
                self.x = player.x + player.width + 1
        else:
            if (
                self.x + self.width > player.x
                and self.x + self.width < player.x + player.width
                and self.y > player.y
                and self.y < player.y + player.height
            ):
                self.direction = 180 - self.direction
                self.speed += 0.2
                self.x = player.x - self.width - 1
        if self.y < 0:
            self.direction = 360 - self.direction
            self.y = abs(self.y)
            if abs(self.direction - 90) < 15:
                self.direction += randrange(0, 30) * randrange(-1, 2, 2)
        elif self.y + self.height > constants.GAME_HEIGHT:
            self.direction = 360 - self.direction
            self.y = (
                constants.GAME_HEIGHT
                - ((self.y + self.height) - constants.GAME_HEIGHT)
                - self.height
            )
            if abs(self.direction - 270) < 15:
                self.direction += randrange(0, 30) * randrange(-1, 2, 2)
        self.direction = self.direction % 360

    async def reset_pos(self):
        self.x = (constants.GAME_WIDTH / 2) - (constants.BALL_SIZE / 2)
        self.y = (constants.GAME_HEIGHT / 2) - (constants.BALL_SIZE / 2)
        self.direction = randrange(120, 210)
        self.speed = constants.BALL_SPEED


@dataclass
class GameState:
    width: int = constants.GAME_WIDTH
    height: int = constants.GAME_HEIGHT
    started: bool = False


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
