import math
from attr import dataclass
from random import randrange
from typing import List
import gameplay.constants as constants


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
