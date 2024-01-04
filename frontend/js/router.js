/**
 * @fileoverview Router for frontend
 * @description Handles routing for frontend to enable SPA.
 * Also handles updating the title and description of the page.
 */
import { updateNavLinks } from "./nav.js";

const TEMPLATE_DIR = "/frontend/templates/";
const JS_DIR = "/frontend/js/";
const TITLE = "ft_transcendence";

document.addEventListener("click", (e) => {
    const { target } = e;
    if (!target.matches("nav a")) {
        return;
    }
    e.preventDefault();
    urlRoute(target);
});

// Route definitions
const urlRoutes = {
    404: {
        template: TEMPLATE_DIR + "404.html",
        title: "Page Not Found | " + TITLE,
        description: "",
    },
    "/": {
        template: TEMPLATE_DIR + "game.html",
        title: "Home | " + TITLE,
        description: "",
        script: JS_DIR + "game.js",
        navLink: "nav-btn-home",
    },
    "/game": {
        template: TEMPLATE_DIR + "game.html",
        title: "Game | " + TITLE,
        description: "",
        script: JS_DIR + "game.js",
        navLink: "nav-btn-game",
    },
    "/tournament": {
        template: TEMPLATE_DIR + "tournament.html",
        title: "Tournament | " + TITLE,
        description: "",
        script: JS_DIR + "tournament.js",
        navLink: "nav-btn-tour",
    },
    "/login": {
        template: TEMPLATE_DIR + "login.html",
        title: "Login | " + TITLE,
        description: "",
        script: JS_DIR + "login.js",
    },
    "/signup": {
        template: TEMPLATE_DIR + "signup.html",
        title: "Sign Up | " + TITLE,
        description: "",
        script: JS_DIR + "signup.js",
    },
};

const urlRoute = (event) => {
    window.history.pushState({}, "", event.href);
    urlLocationHandler();
};

const urlLocationHandler = async () => {
    /**
     * Handle rendering of the actual page. Injects HTML and JS scripts
     * according to route configurations provided in `urlRoutes`.
     */

    // TODO: Remove this line when ready to deploy. Added for local testing
    const location = window.location.pathname.replace(/^\/frontend/, "");

    if (location.length == 0) {
        location = "/";
    }

    // Current defaults to "/" Home page if route not found.
    // TODO: Properly configure 404 page
    const route = urlRoutes[location] || urlRoutes["/"];

    const html = await fetch(route.template).then((response) => response.text());
    document.getElementById("content").innerHTML = html;
    document.title = route.title;
    document
        .querySelector("meta[name='description']")
        .setAttribute("content", route.description);

    updateNavLinks(route);

    if (!route.script) {
        return;
    }
    const script = document.createElement("script");
    script.src = route.script;
    script.id = "pageScript";
    script.type = "module";
    document.getElementById("content").appendChild(script);
};

window.onpopstate = urlLocationHandler;

urlLocationHandler();
