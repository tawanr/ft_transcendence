import math
from random import choice, randrange
from typing import List
from uuid import uuid4

from attr import dataclass

import gameplay.constants as constants
from gameplay.models import GamePlayer, GameRoom


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
    registered_user = None
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

    async def set_ready(self):
        self.ready = True

    async def set_controls(self, up: bool = False, down: bool = False):
        self.up_key = up
        self.down_key = down


@dataclass
class BallState(EntityState):
    direction: int = 0
    score_1: int = 0
    score_2: int = 0

    async def update(self, players: List[PlayerState]):
        assert len(players) == 2
        diff_x = self.speed * math.cos(math.radians(self.direction))
        diff_y = self.speed * math.sin(math.radians(self.direction))
        self.x += diff_x
        self.y += diff_y
        for player in players:
            await self.check_collision(player)
        if self.x <= 0:
            self.score_2 += 1
            player = await GamePlayer.objects.aget(session_id=players[1].player_id)
            player.score += 1
            await player.asave()
            await self.reset_pos()
        elif self.x + self.width >= constants.GAME_WIDTH:
            self.score_1 += 1
            player = await GamePlayer.objects.aget(session_id=players[0].player_id)
            player.score += 1
            await player.asave()
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
        self.direction = (randrange(45, 135) + choice([90, 270])) % 360
        self.speed = constants.BALL_SPEED

    async def check_end(self):
        if self.score_1 >= constants.WIN_SCORE or self.score_2 >= constants.WIN_SCORE:
            await self.reset_pos()
            self.speed = 0
            return 0 if self.score_1 > self.score_2 else 1
        return -1


@dataclass
class GameState:
    width: int = constants.GAME_WIDTH
    height: int = constants.GAME_HEIGHT
    started: bool = False
    players: List[PlayerState] = []
    ball: BallState = None
    room: GameRoom = None

    async def reset_states(self):
        self.players = [
            PlayerState(
                player_id=uuid4(),
                x=constants.PLAYER_LEFT_OFFSET,
                y=(self.height / 2) - (constants.PLAYER_HEIGHT / 2),
                speed=constants.PLAYER_SPEED,
                width=constants.PLAYER_WIDTH,
                height=constants.PLAYER_HEIGHT,
                player1=True,
            ),
            PlayerState(
                player_id=uuid4(),
                x=constants.GAME_WIDTH
                - constants.PLAYER_RIGHT_OFFSET
                - constants.PLAYER_WIDTH,
                y=(self.height / 2) - (constants.PLAYER_HEIGHT / 2),
                speed=constants.PLAYER_SPEED,
                width=constants.PLAYER_WIDTH,
                height=constants.PLAYER_HEIGHT,
                player1=False,
            ),
        ]
        self.ball = BallState(
            x=(constants.GAME_WIDTH / 2) - (constants.BALL_SIZE / 2),
            y=(constants.GAME_HEIGHT / 2) - (constants.BALL_SIZE / 2),
            width=constants.BALL_SIZE,
            height=constants.BALL_SIZE,
        )

    async def get_player(self, player_id: str):
        for player in self.players:
            if str(player.player_id) == player_id:
                return player
        return None

    async def start(self):
        self.started = True
        self.room.is_started = True

    async def update(self):
        if not self.room.is_started and not self.room.is_active:
            return None
        if (victor := await self.ball.check_end()) >= 0:
            self.started = False
            winner_id = self.players[victor].player_id
            await self.room.victory(winner_id)
            return winner_id
        return None
