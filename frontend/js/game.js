import * as constants from "./constants.js";

var canvas = document.getElementById("gameArea");
var ctx = canvas.getContext("2d");
var player1Up = false;
var player1Down = false;
var player2Up = false;
var player2Down = false;
var gameStarted = false;
var playerReady = false;

class GameEntity {
    constructor(x, y, width, height, color) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.color = color;
    }
}

class Player extends GameEntity {
    constructor(x, y, width, height, color, name) {
        super(x, y, width, height, color);
        this.score = 0;
        this.name = name;
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
}

class PongBall extends GameEntity {
    constructor(x, y, width, height, color, speed, direction) {
        super(x, y, width, height, color);
        this.speed = speed;
        this.direction = direction;
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
        if (this.x + this.width > canvas.width) {
            player1.incrementScore();
            this.resetPos();
        }
        if (this.y + this.height > canvas.height) {
            this.y = canvas.height - (this.y - canvas.height);
            this.direction = 360 - this.direction;
            if (Math.abs(this.direction - 270) < 15) {
                this.direction += Math.random() * 120 * (this.direction > 270 ? 1 : -1);
            }
        }
    }

    resetPos() {
        this.x = canvas.width / 2;
        this.y = canvas.height / 2;
        this.direction = Math.random() * 360;
    }
}

var player1 = new Player(
    constants.PLAYER_LEFT_OFFSET,
    canvas.height / 2 - constants.PLAYER_HEIGHT / 2,
    constants.PLAYER_WIDTH,
    constants.PLAYER_HEIGHT,
    "#0095DD",
    "Player 1"
);
var player2 = new Player(
    canvas.width - constants.PLAYER_RIGHT_OFFSET - constants.PLAYER_WIDTH,
    canvas.height / 2 - constants.PLAYER_HEIGHT / 2,
    constants.PLAYER_WIDTH,
    constants.PLAYER_HEIGHT,
    "#FF0000",
    "Player 2"
);
var ball = new PongBall(
    canvas.width / 2,
    canvas.height / 2,
    constants.BALL_SIZE,
    constants.BALL_SIZE,
    "#000000",
    0,
    Math.random() * 60 + 120 + Math.round(Math.random()) * 180
);

var gameSocket;

var playerId = "";

function gameInit() {
    gameSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        if (data.type === "roomDetails") {
            playerId = data.playerId;
            document.getElementById("gameRoomTitle").innerText = data.roomCode;
            document.getElementById("userRoomNav").classList.add("d-none");
        }

        if (data.type === "playerId") {
            playerId = data.playerId;
        }

        if (data.type === constants.SOCKET_GAMESTATE) {
            player1.x = data.player1.x;
            player1.y = data.player1.y;
            player1.score = data.player1.score;
            player2.x = data.player2.x;
            player2.y = data.player2.y;
            player2.score = data.player2.score;
            ball.x = data.ball.x;
            ball.y = data.ball.y;
            updateScoreBoard();
        }
    };
}

function registerClient(playerName) {
    gameSocket.onopen = function (e) {
        gameSocket.send(
            JSON.stringify({
                type: constants.SOCKET_REGISTER,
                playerName: playerName,
            })
        );
    }
}

function joinRoom() {
    const playerName = document.getElementById("playerName").value;
    const roomCode = document.getElementById("roomCode").value;
    gameSocket = new WebSocket(
        "ws://" + constants.BACKEND_HOST + constants.BACKEND_SOCKET_API + roomCode + "/"
    );
    registerClient(playerName);
    gameInit();
}
document.getElementById("joinRoomBtn").addEventListener("click", joinRoom);

function createRoom() {
    const playerName = document.getElementById("playerName").value;
    gameSocket = new WebSocket(
        "ws://" + constants.BACKEND_HOST + constants.BACKEND_SOCKET_API
    );
    registerClient(playerName);
    gameInit();
}
document.getElementById("createRoomBtn").addEventListener("click", createRoom);

function playerSendReady() {
    playerReady = true;
    gameSocket.send(
        JSON.stringify({
            type: constants.SOCKET_READY,
            id: playerId,
        })
    );
}

var player1Score = document.getElementById("player1Score");
var player2Score = document.getElementById("player2Score");

document.addEventListener("keydown", keyDownHandler, false);
document.addEventListener("keyup", keyUpHandler, false);
function keyDownHandler(e) {
    var changed = false;
    if (e.keyCode == constants.KEY_UP) {
        changed = player1Up == false;
        player1Up = true;
    } else if (e.keyCode == constants.KEY_DOWN) {
        changed = player1Down == false;
        player1Down = true;
    }

    if (e.keyCode == 87) {
        player2Up = true;
    } else if (e.keyCode == 83) {
        player2Down = true;
    }
    if (e.keyCode == constants.KEY_SPACE && gameStarted == false) {
        if (!playerReady) {
            playerSendReady();
        }
    }

    if (!changed) {
        return;
    }

    gameSocket.send(
        JSON.stringify({
            type: constants.SOCKET_PLAYER_CONTROLS,
            up: player1Up,
            down: player1Down,
            id: playerId,
        })
    );
}

function keyUpHandler(e) {
    var changed = false;
    if (e.keyCode == constants.KEY_UP) {
        changed = true;
        player1Up = false;
    } else if (e.keyCode == constants.KEY_DOWN) {
        changed = true;
        player1Down = false;
    }

    if (e.keyCode == 87) {
        player2Up = false;
    } else if (e.keyCode == 83) {
        player2Down = false;
    }

    if (!changed) {
        return;
    }

    gameSocket.send(
        JSON.stringify({
            type: constants.SOCKET_PLAYER_CONTROLS,
            up: player1Up,
            down: player1Down,
            id: playerId,
        })
    );
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#b8c9bc";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // if (player1Up && player1.y > 0) {
    //     player1.y -= 2;
    // }
    // else if (player1Down && player1.y < canvas.height - player1.height) {
    //     player1.y += 2;
    // }
    ctx.strokeStyle = "black";
    ctx.beginPath();
    ctx.fillStyle = player1.color;
    ctx.rect(player1.x, player1.y, player1.width, player1.height);
    ctx.fill();
    ctx.stroke();

    // if (player2Up && player2.y > 0) {
    //     player2.y -= 2;
    // }
    // else if (player2Down && player2.y < canvas.height - player2.height) {
    //     player2.y += 2;
    // }
    ctx.beginPath();
    ctx.fillStyle = player2.color;
    ctx.rect(player2.x, player2.y, player2.width, player2.height);
    ctx.fill();
    ctx.stroke();

    // ball.update()
    ctx.fillStyle = ball.color;
    ctx.fillRect(ball.x, ball.y, ball.width, ball.height);

    requestAnimationFrame(draw);
}

function updateScoreBoard() {
    player1Score.innerHTML = player1.name + " : " + player1.score;
    player2Score.innerHTML = player2.name + " : " + player2.score;
}
draw();
