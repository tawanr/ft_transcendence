export class GameHistory {
    /**
     * Object for a game history.
     * @param {string} player1Name
     * @param {string} player1Avatar
     * @param {string} player2Name
     * @param {string} player2Avatar
     * @param {boolean} isFinished
     * @param {string} score
     * @param {boolean} isWinner
     * @param {string} date
     */
    constructor(
        player1Name,
        player1Avatar,
        player2Name,
        player2Avatar,
        isFinished,
        score,
        isWinner,
        date
    ) {
        this.player1Name = player1Name;
        this.player1Avatar = player1Avatar;
        this.player2Name = player2Name;
        this.player2Avatar = player2Avatar;
        this.isFinished = isFinished;
        this.score = score;
        this.isWinner = isWinner;
        this.date = date;
    }
}
