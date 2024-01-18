import { fetchHTML } from "../../js/utils.js";
import { PongGame } from "./pong.game.js";

class PongElement extends HTMLElement {
    static observedAttributes = [];

    constructor() {
        super();
        this.rendered = false;
        this.shadow = this.attachShadow({ mode: "closed" });
        fetchHTML("/components/pong/pong.html").then((html) => {
            this.render(html);
            this.setupGame();
        });
    }

    connectedCallback() {}

    attributeChangedCallback(name, oldValue, newValue) {}

    setupGame() {
        this.game = new PongGame(this.shadow);
        this.game.renderMode = "3d";
        this.game.setup();

        document.addEventListener(
            "keydown",
            (e) => {
                this.game.keyDownHandler(e);
            },
            false
        );
        document.addEventListener(
            "keyup",
            (e) => {
                this.game.keyUpHandler(e);
            },
            false
        );
    }

    roomBtnHandler() {
        this.game.connectRoom();
    }

    render(html) {
        if (!html) {
            return;
        }
        this.shadow.innerHTML = html;
    }
}

customElements.define("pong-game", PongElement);
