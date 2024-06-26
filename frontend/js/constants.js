// SERVER CONFIGS
export const BACKEND_SERVER_IP = location.hostname;

export const BACKEND_HOST = `https://${BACKEND_SERVER_IP}:${location.port}/api`;
export const BACKEND_SOCKET_HOST = `wss://${BACKEND_SERVER_IP}:${location.port}/wsapi`;
export const BACKEND_SOCKET_API = "/ws/gameplay/";
export const BACKEND_CHATSOCKET_API = "/ws/user/";
export const BACKEND_TOURNAMENT_API = "/gameplay/tournament/";
export const BACKEND_CHATROOM_API = "/ws/chatroom/";
export const BACKEND_NOTIFICATION_API = "/ws/notification/";

// GAME DEFAULT VALUES
export const PLAYER_LEFT_OFFSET = 40;
export const PLAYER_RIGHT_OFFSET = 40;
export const PLAYER_WIDTH = 10;
export const PLAYER_HEIGHT = 100;
export const BALL_SIZE = 10;
export const BALL_SPEED = 3;
export const KEY_UP = 38;
export const KEY_DOWN = 40;
export const KEY_SPACE = 32;
export const GAME_WIDTH = 800;
export const GAME_HEIGHT = 600;

// GAME WEB SOCKET CODES
export const SOCKET_REGISTER = "client.register";
export const SOCKET_GAMESTATE = "gameState";
export const SOCKET_READY = "player.ready";
export const SOCKET_PLAYER_CONTROLS = "player.controls";

// ASSETS
export const USER_AVATAR = "static/42_Logo.png";
