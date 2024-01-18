import * as constants from "../../js/constants.js";
import { Player, PongBall } from "./pong.states.js";

export class PongGame {
    gameSocket;

    constructor(document) {
        // Set up DOM
        this.document = document;

        this.player1 = new Player();
        this.player2 = new Player("player2");
        this.ball = new PongBall();
        this.playerId = "";
        this.localGame = false;

        this.canvas = this.document.getElementById("gameArea");
        this.ctx = this.canvas.getContext("2d");
        this.player1Up = false;
        this.player1Down = false;
        this.player2Up = false;
        this.player2Down = false;
        this.gameStarted = false;
        this.playerReady = false;
    }

    initClient() {
        this.gameSocket.onopen = (e) => {
            this.registerClient(e);
        };
        this.gameSocket.onmessage = (e) => {
            this.socketHandler(e);
        };
    }

    registerClient() {
        const playerName = this.document.getElementById("playerName").value;
        this.gameSocket.send(
            JSON.stringify({
                type: constants.SOCKET_REGISTER,
                playerName: playerName,
                authorization: localStorage.getItem("token") || null,
            })
        );
    }

    connectRoom() {
        const roomCode = this.document.getElementById("roomCode").value;
        let api_url = constants.BACKEND_SOCKET_HOST + constants.BACKEND_SOCKET_API;
        if (roomCode) {
            api_url += roomCode + "/";
        }
        this.gameSocket = new WebSocket(api_url);
        this.initClient();
    }

    pageSetup() {
        const nameInput = this.document.querySelector("#userRoomNav .nameInput");
        if (localStorage.getItem("token")) {
            nameInput.classList.add("d-none");
        }
    }

    setup() {
        this.pageSetup();

        this.document.getElementById("joinRoomBtn").addEventListener("click", () => {
            this.connectRoom();
        });
        this.document.getElementById("createRoomBtn").addEventListener("click", () => {
            this.connectRoom();
        });
    }

    localUpdate() {
        if (this.player1Up && this.player1.y > 0) {
            this.player1.y -= 2;
        } else if (
            this.player1Down &&
            this.player1.y < this.canvas.height - this.player1.height
        ) {
            this.player1.y += 2;
        }
        if (this.player2Up && this.player2.y > 0) {
            this.player2.y -= 2;
        } else if (
            this.player2Down &&
            this.player2.y < this.canvas.height - this.player2.height
        ) {
            this.player2.y += 2;
        }
        this.ball.update();
    }

    draw() {
        // For local game, need to update draw calls to support without socket game states
        // if (this.localGame) {
        //     this.localUpdate();
        // }

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = "#b8c9bc";
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        this.ctx.strokeStyle = "black";

        // Draw Player 1
        this.ctx.beginPath();
        this.ctx.fillStyle = this.player1.color;
        this.ctx.rect(
            this.player1.x,
            this.player1.y,
            this.player1.width,
            this.player1.height
        );
        this.ctx.fill();
        this.ctx.stroke();

        // Draw Player 2
        this.ctx.beginPath();
        this.ctx.fillStyle = this.player2.color;
        this.ctx.rect(
            this.player2.x,
            this.player2.y,
            this.player2.width,
            this.player2.height
        );
        this.ctx.fill();
        this.ctx.stroke();

        // Draw game ball
        this.ctx.fillStyle = this.ball.color;
        this.ctx.fillRect(this.ball.x, this.ball.y, this.ball.width, this.ball.height);

        // requestAnimationFrame(this.draw);
    }

    playerSendReady() {
        this.playerReady = true;
        this.gameSocket.send(
            JSON.stringify({
                type: constants.SOCKET_READY,
                id: this.playerId,
            })
        );
    }

    socketSendControls() {
        this.gameSocket.send(
            JSON.stringify({
                type: constants.SOCKET_PLAYER_CONTROLS,
                up: this.player1Up,
                down: this.player1Down,
                id: this.playerId,
            })
        );
    }

    keyDownHandler(e) {
        var changed = false;
        if (e.keyCode == constants.KEY_UP) {
            changed = this.player1Up == false;
            this.player1Up = true;
        } else if (e.keyCode == constants.KEY_DOWN) {
            changed = this.player1Down == false;
            this.player1Down = true;
        }

        if (e.keyCode == 87) {
            this.player2Up = true;
        } else if (e.keyCode == 83) {
            this.player2Down = true;
        }
        if (e.keyCode == constants.KEY_SPACE && this.gameStarted == false) {
            if (!this.playerReady) {
                this.playerSendReady();
            }
        }

        if (changed) {
            this.socketSendControls();
        }
    }

    keyUpHandler(e) {
        var changed = false;
        if (e.keyCode == constants.KEY_UP) {
            changed = true;
            this.player1Up = false;
        } else if (e.keyCode == constants.KEY_DOWN) {
            changed = true;
            this.player1Down = false;
        }

        if (e.keyCode == 87) {
            this.player2Up = false;
        } else if (e.keyCode == 83) {
            this.player2Down = false;
        }

        if (changed) {
            this.socketSendControls();
        }
    }

    socketHandler(e) {
        const data = JSON.parse(e.data);
        if (data.type === "roomDetails") {
            this.playerId = data.playerId;
            this.document.getElementById("playerStatus").innerText = data.roomCode;
            this.document.getElementById("userRoomNav").classList.add("d-none");
        }

        if (data.type === "playerId") {
            this.playerId = data.playerId;
        }

        if (data.type === "gameEnd") {
            const playerState = this.document.getElementById("playerStatus");
            if (data.winnerId == this.playerId) {
                playerState.innerText = "You won!";
                playerState.classList.add("text-success");
            } else {
                playerState.innerText = "You lost.";
                playerState.classList.add("text-danger");
            }
        }

        if (data.type === constants.SOCKET_GAMESTATE) {
            this.player1.x = data.player1.x;
            this.player1.y = data.player1.y;
            this.player1.score = data.player1.score;
            this.player2.x = data.player2.x;
            this.player2.y = data.player2.y;
            this.player2.score = data.player2.score;
            this.ball.x = data.ball.x;
            this.ball.y = data.ball.y;
            this.player1.name = data.player1.name || "Player 1";
            this.player2.name = data.player2.name || "Player 2";

            this.draw();
            this.updateScoreBoard();
        }
    }

    updateScoreBoard() {
        const player1Name = this.document.getElementById("player1Name");
        const player2Name = this.document.getElementById("player2Name");
        const player1Score = this.document.getElementById("player1Score");
        const player2Score = this.document.getElementById("player2Score");

        player1Name.innerText = this.player1.name;
        player2Name.innerText = this.player2.name;
        player1Score.innerText = this.player1.score;
        player2Score.innerText = this.player2.score;
    }
}
