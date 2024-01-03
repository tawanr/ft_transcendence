document.addEventListener("click", (e) => {
  const { target } = e;
  if (!target.matches("nav a")) {
    return;
  }
  e.preventDefault();
  urlRoute(target);
});

const TEMPLATE_DIR = "/frontend/templates/";
const JS_DIR = "/frontend/js/";
const TITLE = "ft_transcendence";

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
  const location = window.location.pathname.replace(/^\/frontend/, "");
  if (location.length == 0) {
    location = "/";
  }

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

function updateNavLinks(route) {
  const navLink = document.querySelector(".nav-link.active");
  if (navLink) {
    navLink.classList.remove("active");
  }
  if ("navLink" in route) {
    document.getElementById(route.navLink).classList.add("active");
  }
}

window.onpopstate = urlLocationHandler;

urlLocationHandler();
