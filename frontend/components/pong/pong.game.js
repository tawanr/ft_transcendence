import * as constants from "../../js/constants.js";
import * as THREE from "three";
import { Player, PongBall } from "./pong.states.js";

/**
 * Encapsulates the entire pong game with all states and methods.
 */
export class PongGame {
    gameSocket;

    /**
     * Represents a Pong game.
     * @constructor
     * @param {HTMLElement} document - The shadow DOM of the game element.
     */
    constructor(document, localGame) {
        // Set up DOM. This is due to the fact that the game is rendered in a shadow DOM
        // so we can't access the DOM directly from the game.
        this.document = document;
        this.localGame = localGame || false;

        // Init all default states.
        this.player1 = new Player();
        this.player2 = new Player("player2");
        this.ball = new PongBall();
        this.playerId = "";
        this.renderMode = "2d";

        this.canvas = this.document.getElementById("gameArea");
        this.ctx = this.canvas.getContext("3d");
        this.player1Up = false;
        this.player1Down = false;
        this.player2Up = false;
        this.player2Down = false;
        this.gameStarted = false;
        this.playerReady = false;
    }

    /**
     * Init the game socket and register the client.
     */
    initClient() {
        this.gameSocket.onopen = (e) => {
            this.registerClient(e);
        };
        this.gameSocket.onmessage = (e) => {
            this.socketHandler(e);
        };
    }

    /**
     * Register the client to the game socket.
     * If not done, the server will disconnect the client automatically.
     */
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

    /**
     * Connect to the game socket.
     * If room code is provided, connect to the room.
     * Otherwise, connect to a new room.
     */
    connectRoom(roomCode = null) {
        let api_url = constants.BACKEND_SOCKET_HOST + constants.BACKEND_SOCKET_API;
        if (roomCode) {
            api_url += roomCode + "/";
        }
        this.gameSocket = new WebSocket(api_url);
        this.initClient();
    }

    /**
     * Set up the page.
     * If the user is logged in, hide the name input.
     */
    pageSetup() {
        const nameInput = this.document.querySelector("#userRoomNav .nameInput");
        if (localStorage.getItem("token")) {
            nameInput.classList.add("d-none");
        }
        if (this.localGame) {
            this.document.getElementById("userRoomNav").classList.add("d-none");
        }
        if (this.renderMode === "3d" && !this.localGame) {
            this.ctx = this.canvas.getContext("3d");
            this.init3d();
        } else {
            this.ctx = this.canvas.getContext("2d");
            this.draw();
        }
    }

    /**
     * Set up the game.
     * Add event listeners to the buttons.
     */
    setup() {
        this.pageSetup();

        // Add event listeners' callbacks are wrapped in arrow functions to preserve
        // the `this` context. Otherwise, `this` will refer to the event target.
        // Alternatively, we can use `bind` to bind the `this` context to the callback.
        if (this.localGame) {
            return;
        }
        this.document.getElementById("joinRoomBtn").addEventListener("click", () => {
            const roomCode = this.document.getElementById("roomCode").value;
            this.connectRoom(roomCode);
        });
        this.document.getElementById("createRoomBtn").addEventListener("click", () => {
            this.connectRoom();
        });
    }

    /**
     * Update the game state for local game.
     */
    localUpdate() {
        if (this.player1Up && this.player1.y > 0) {
            this.player1.y -= 5;
        } else if (
            this.player1Down &&
            this.player1.y < this.canvas.height - this.player1.height
        ) {
            this.player1.y += 5;
        }
        if (this.player2Up && this.player2.y > 0) {
            this.player2.y -= 5;
        } else if (
            this.player2Down &&
            this.player2.y < this.canvas.height - this.player2.height
        ) {
            this.player2.y += 5;
        }
        this.ball.update(this.player1, this.player2, this.updateScoreBoard.bind(this));
    }

    /**
     * Draw loop for the game state as 2D rendering.
     */
    draw() {
        // For local game, need to update draw calls to support without socket game states
        if (this.localGame) {
            this.localUpdate();
        }
        requestAnimationFrame(() => {
            this.draw();
        });

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

    /**
     * Setup Three.js scene and all objects. Initiate the draw loop.
     */
    init3d() {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, 800 / 600, 1, 500);
        camera.position.set(0, 8.6, 2.5);
        camera.lookAt(0, 0, 0);

        this.ctx = this.canvas.getContext("3d");
        const renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            context: this.ctx,
            antialias: true,
        });
        renderer.shadowMap.enabled = true;

        const planeGeometry = new THREE.BoxGeometry(8, 1, 6);
        const planeMaterial = new THREE.MeshStandardMaterial({ color: 0xeeeeee });
        const plane = new THREE.Mesh(planeGeometry, planeMaterial);
        plane.receiveShadow = true;
        scene.add(plane);

        const topWallGeometry = new THREE.BoxGeometry(12, 3, 10);
        const topWallMaterial = new THREE.MeshStandardMaterial({ color: 0x333333 });
        const topWallMesh = new THREE.Mesh(topWallGeometry, topWallMaterial);
        topWallMesh.receiveShadow = true;
        topWallMesh.position.set(0, 1.5, 8);
        scene.add(topWallMesh);

        const bottomWallGeometry = new THREE.BoxGeometry(12, 3, 10);
        const bottomWallMaterial = new THREE.MeshStandardMaterial({ color: 0x333333 });
        const bottomWallMesh = new THREE.Mesh(bottomWallGeometry, bottomWallMaterial);
        bottomWallMesh.receiveShadow = true;
        bottomWallMesh.position.set(0, 1.5, -8);
        scene.add(bottomWallMesh);

        const player1Geometry = new THREE.BoxGeometry(
            this.player1.width / 100,
            0.1,
            this.player1.height / 100
        );
        const player1Material = new THREE.MeshStandardMaterial({ color: 0x0095dd });
        const player1Mesh = new THREE.Mesh(player1Geometry, player1Material);
        player1Mesh.castShadow = true;
        player1Mesh.position.set(
            this.player1.x / 100 - 4 - this.player1.width / 200,
            0.9,
            this.player1.y / 100 - 3 + this.player1.height / 200
        );
        scene.add(player1Mesh);

        const player2Geometry = new THREE.BoxGeometry(
            this.player2.width / 100,
            0.1,
            this.player2.height / 100
        );
        const player2Material = new THREE.MeshStandardMaterial({ color: 0xff0000 });
        const player2Mesh = new THREE.Mesh(player2Geometry, player2Material);
        player2Mesh.castShadow = true;
        player2Mesh.position.set(
            this.player2.x / 100 - 4 + this.player2.width / 200,
            0.9,
            this.player2.y / 100 - 3 + this.player2.height / 200
        );
        scene.add(player2Mesh);

        const ballGeometry = new THREE.SphereGeometry(constants.BALL_SIZE / 100);
        const ballMaterial = new THREE.MeshStandardMaterial({ color: 0x666666 });
        const ballMesh = new THREE.Mesh(ballGeometry, ballMaterial);
        ballMesh.castShadow = true;
        ballMesh.position.set(
            this.ball.x / 100 - 4,
            0.9,
            this.ball.y / 100 - 3 - this.ball.height / 200
        );
        scene.add(ballMesh);

        const globalLight = new THREE.AmbientLight(0xffffff, 0.8);
        scene.add(globalLight);

        const light = new THREE.PointLight(0xffffff, 1, 50, 0.2);
        light.position.set(0, 8, 0);
        light.castShadow = true;
        scene.add(light);
        this.draw3d(player1Mesh, player2Mesh, ballMesh, scene, camera, renderer);
    }

    /**
     * Three.js animation loop.
     * @param {THREE.Mesh} player1Mesh - Mesh for player 1.
     * @param {THREE.Mesh} player2Mesh - Mesh for player 2.
     * @param {THREE.Mesh} ballMesh - Mesh for the ball.
     * @param {THREE.Scene} scene - Scene object.
     * @param {THREE.PerspectiveCamera} camera - Camera object.
     * @param {THREE.WebGLRenderer} renderer - Renderer object.
     */
    draw3d(player1Mesh, player2Mesh, ballMesh, scene, camera, renderer) {
        requestAnimationFrame(() => {
            this.draw3d(player1Mesh, player2Mesh, ballMesh, scene, camera, renderer);
        });

        player1Mesh.position.set(
            this.player1.x / 100 - 4 - this.player1.width / 200,
            0.9,
            this.player1.y / 100 - 3 + this.player1.height / 200
        );
        player2Mesh.position.set(
            this.player2.x / 100 - 4 + this.player2.width / 200,
            0.9,
            this.player2.y / 100 - 3 + this.player2.height / 200
        );
        ballMesh.position.set(this.ball.x / 100 - 4, 0.9, this.ball.y / 100 - 3);
        const cameraTarget = new THREE.Vector3(ballMesh.position.x / 10, 0, 0);
        renderer.render(scene, camera);
    }

    /**
     * Send a ready signal to the server.
     */
    playerSendReady() {
        this.playerReady = true;
        if (this.localGame) {
            this.ball.speed = 5;
            return;
        }
        this.gameSocket.send(
            JSON.stringify({
                type: constants.SOCKET_READY,
                id: this.playerId,
            })
        );
    }

    /**
     * Send the player's controls to the server.
     */
    socketSendControls() {
        if (this.localGame) {
            return;
        }
        this.gameSocket.send(
            JSON.stringify({
                type: constants.SOCKET_PLAYER_CONTROLS,
                up: this.player1Up,
                down: this.player1Down,
                id: this.playerId,
            })
        );
    }

    /**
     * Event handler for keydown events.
     * @param {Event} e - Keydown event.
     */
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

    /**
     * Event handler for keyup events.
     * @param {Event} e - Keyup event.
     */
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

    /**
     * Event handler for socket messages.
     * @param {Event} e
     */
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

            this.updateScoreBoard();
        }
    }

    /**
     * Update the scoreboard.
     */
    updateScoreBoard() {
        const player1Name = this.document.getElementById("player1Name");
        const player2Name = this.document.getElementById("player2Name");
        const player1Score = this.document.getElementById("player1Score");
        const player2Score = this.document.getElementById("player2Score");

        player1Name.innerText = this.player1.name;
        player2Name.innerText = this.player2.name;
        player1Score.innerText = this.player1.score;
        player2Score.innerText = this.player2.score;

        if (!this.localGame) {
            return;
        }
        const playerState = this.document.getElementById("playerStatus");
        playerState.classList.add("text-success");
        if (this.player1.score >= 5) {
            playerState.innerText = "Player 1 won!";
            this.ball.gameEnd = true;
        } else if (this.player2.score >= 5) {
            playerState.innerText = "Player 2 won!";
            this.ball.gameEnd = true;
        }
    }
}
