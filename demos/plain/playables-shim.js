/**
 * Standalone browser fallback for samples that expect the YouTube Playables SDK.
 * The real SDK is left untouched inside an actual Playables environment.
 */
(() => {
  const existing = window.ytgame;

  if (existing?.IN_PLAYABLES_ENV) {
    return;
  }

  const storageKey = "web-game-samples.playables-save";
  const listeners = new Map();

  const subscribe = (eventName, callback) => {
    if (typeof callback !== "function") {
      return () => {};
    }

    window.addEventListener(eventName, callback);
    listeners.set(callback, { eventName, callback });

    return () => {
      const listener = listeners.get(callback);
      if (listener) {
        window.removeEventListener(listener.eventName, listener.callback);
        listeners.delete(callback);
      }
    };
  };

  const game = {
    ...(existing?.game ?? {}),
    firstFrameReady() {},
    gameReady() {},
    async loadData() {
      try {
        return window.localStorage.getItem(storageKey) ?? "";
      } catch {
        return "";
      }
    },
    async saveData(value) {
      try {
        window.localStorage.setItem(storageKey, String(value));
      } catch {
        // Storage can be unavailable in strict privacy contexts; gameplay continues.
      }
    },
  };

  const system = {
    ...(existing?.system ?? {}),
    onPause(callback) {
      return subscribe("blur", callback);
    },
    onResume(callback) {
      return subscribe("focus", callback);
    },
    onAudioEnabledChange() {
      return () => {};
    },
    isAudioEnabled() {
      return true;
    },
    async getLanguage() {
      return navigator.language || "en";
    },
  };

  window.ytgame = {
    ...(existing ?? {}),
    SDK_VERSION: existing?.SDK_VERSION ?? "standalone-web-shim-v1",
    IN_PLAYABLES_ENV: false,
    game,
    system,
    engagement: {
      ...(existing?.engagement ?? {}),
      sendScore() {},
    },
    ads: {
      ...(existing?.ads ?? {}),
      async requestInterstitialAd() {},
      async requestRewardedAd() {
        return false;
      },
    },
    health: {
      ...(existing?.health ?? {}),
      logError() {},
    },
  };
})();
