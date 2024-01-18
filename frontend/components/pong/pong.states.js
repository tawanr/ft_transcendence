import * as constants from "../../js/constants.js";

class GameEntity {
    constructor(x, y, width, height, color) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.color = color;
    }
}

export class Player extends GameEntity {
    constructor(playerType = "player1") {
        super();
        this.resetDefaults(playerType);
    }

    incrementScore() {
        this.score++;
    }

    checkCollision(entity) {
        if (
            this.x < entity.x + entity.width &&
            this.x + this.width > entity.x &&
            this.y < entity.y + entity.height &&
            this.y + this.height > entity.y
        ) {
            return true;
        }
        return false;
    }

    resetDefaults(player = "player1") {
        this.score = 0;
        this.width = constants.PLAYER_WIDTH;
        this.height = constants.PLAYER_HEIGHT;
        this.y = constants.GAME_HEIGHT / 2 - constants.PLAYER_HEIGHT / 2;
        this.x = constants.PLAYER_LEFT_OFFSET;
        this.color = "#0095DD";
        this.name = "Player 1";
        if (player === "player2") {
            this.x =
                constants.GAME_WIDTH -
                constants.PLAYER_RIGHT_OFFSET -
                constants.PLAYER_WIDTH;
            this.color = "#FF0000";
            this.name = "Player 2";
        }
    }
}

export class PongBall extends GameEntity {
    constructor() {
        super();
        this.resetDefaults();
    }

    resetDefaults() {
        this.x = constants.GAME_WIDTH / 2;
        this.y = constants.GAME_HEIGHT / 2;
        this.width = constants.BALL_SIZE;
        this.height = constants.BALL_SIZE;
        this.color = "#000000";
        this.speed = 0;
        this.direction = Math.random() * 60 + 120 + Math.round(Math.random()) * 180;
    }

    update() {
        let x = this.speed * Math.cos(this.direction * (Math.PI / 180));
        let y = this.speed * Math.sin(this.direction * (Math.PI / 180));
        this.x += x;
        this.y += y;
        this.direction = this.direction % 360;
        if (this.x < 0) {
            player2.incrementScore();
            this.resetPos();
        }
        if (player1.checkCollision(this) || player2.checkCollision(this)) {
            this.direction = 180 - this.direction;
        }
        if (this.y < 0) {
            this.y = Math.abs(this.y);
            this.direction = 360 - this.direction;
            if (Math.abs(this.direction - 90) < 15) {
                this.direction += Math.random() * 30 * (this.direction > 90 ? 1 : -1);
            }
        }
        if (this.x + this.width > constants.GAME_WIDTH) {
            player1.incrementScore();
            this.resetPos();
        }
        if (this.y + this.height > constants.GAME_HEIGHT) {
            this.y = constants.GAME_HEIGHT - (this.y - constants.GAME_HEIGHT);
            this.direction = 360 - this.direction;
            if (Math.abs(this.direction - 270) < 15) {
                this.direction += Math.random() * 120 * (this.direction > 270 ? 1 : -1);
            }
        }
    }

    resetPos() {
        this.x = constants.GAME_WIDTH / 2;
        this.y = constants.GAME_HEIGHT / 2;
        this.direction = Math.random() * 360;
    }
}
