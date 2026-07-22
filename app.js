const games = Object.freeze({
  phaser: {
    title: "Basketball Shoot Out — Phaser 3",
    path: "./demos/phaser/",
  },
  pixijs: {
    title: "Playables SDK Demo — PixiJS 8",
    path: "./demos/pixijs/",
  },
  plain: {
    title: "Canvas Integration Demo — Vanilla Web",
    path: "./demos/plain/",
  },
});

const dialog = document.querySelector("#player-dialog");
const frame = document.querySelector("#game-frame");
const playerTitle = document.querySelector("#player-title");
const externalLink = document.querySelector("#external-link");
const closeButton = document.querySelector("#close-button");
const fullscreenButton = document.querySelector("#fullscreen-button");

function openGame(gameId) {
  const game = games[gameId];
  if (!game || !(dialog instanceof HTMLDialogElement) || !(frame instanceof HTMLIFrameElement)) {
    return;
  }

  playerTitle.textContent = game.title;
  externalLink.href = game.path;
  frame.src = game.path;
  frame.title = game.title;
  dialog.showModal();
  document.body.style.overflow = "hidden";
}

function closeGame() {
  if (!(dialog instanceof HTMLDialogElement)) {
    return;
  }

  dialog.close();
  frame.src = "about:blank";
  document.body.style.overflow = "";
}

document.querySelectorAll("[data-play]").forEach((button) => {
  button.addEventListener("click", () => openGame(button.dataset.play));
});

closeButton?.addEventListener("click", closeGame);

dialog?.addEventListener("click", (event) => {
  if (event.target === dialog) {
    closeGame();
  }
});

dialog?.addEventListener("cancel", (event) => {
  event.preventDefault();
  closeGame();
});

fullscreenButton?.addEventListener("click", async () => {
  const shell = dialog?.querySelector(".player-shell");
  if (!shell) return;

  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    } else {
      await shell.requestFullscreen();
    }
  } catch (error) {
    console.warn("Fullscreen request failed", error);
  }
});

async function showBuildInfo() {
  const status = document.querySelector("#build-status");
  const detail = document.querySelector("#build-detail");

  try {
    const response = await fetch("./build-info.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const info = await response.json();
    const shortRevision = String(info.upstreamRevision ?? "unknown").slice(0, 8);
    const builtAt = new Intl.DateTimeFormat("ja-JP", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(info.builtAt));

    status.innerHTML = `<strong>●</strong> built ${builtAt}`;
    detail.textContent = `upstream revision: ${shortRevision}`;
  } catch (error) {
    console.warn("Build metadata is unavailable", error);
    status.innerHTML = "<strong>●</strong> production build";
    detail.textContent = "upstream revision: metadata unavailable";
  }
}

showBuildInfo();
