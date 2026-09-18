// Runs the inline <script> of project/web/yandex_shell.html in a mocked browser
// and a mocked Yandex SDK, and asserts the bridge contract yandex_sdk.gd
// depends on: the buffered handover, the ad callbacks that must always land,
// the save key, and every path that has to release the game when the platform
// is absent or silent.
//
// This exists because nothing else can execute the shell. Godot's tests read it
// as text and pack_yandex_zip.py reads the built page as text; both only prove
// that certain substrings survived an export, not that the JavaScript works.
//
//   node tools/build/check_yandex_shell.mjs
//
// Needs Node (no packages). Optional - the Godot and Python checks do not
// depend on it.
import fs from "node:fs";
import path from "node:path";
import url from "node:url";
import vm from "node:vm";

const ROOT = path.resolve(path.dirname(url.fileURLToPath(import.meta.url)), "..", "..");
const SHELL = path.join(ROOT, "project", "web", "yandex_shell.html");

const html = fs.readFileSync(SHELL, "utf8");
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
if (blocks.length !== 1) throw new Error("expected exactly one inline script, got " + blocks.length);
const source = blocks[0]
  .replace("$GODOT_CONFIG", "{ canvasResizePolicy: 2 }")
  .replace("$GODOT_THREADS_ENABLED", "false");

function makeElement(id) {
  const classes = new Set();
  return {
    id, textContent: "", style: {},
    classList: {
      add: (c) => classes.add(c), remove: (c) => classes.delete(c),
      contains: (c) => classes.has(c), _all: classes,
    },
    _attrs: {},
    getAttribute(n) { return this._attrs[n] ?? null; },
    setAttribute(n, v) { this._attrs[n] = v; },
  };
}

function buildContext({ withSdk, touch, portrait, missingFeatures = [], startFails = false }) {
  const log = [];
  const i18nNodes = ["title", "rotate", "noCanvas", "loading"].map((k) => {
    const el = makeElement("i18n-" + k);
    el.setAttribute("data-i18n", k);
    return el;
  });
  const byId = {
    boot: makeElement("boot"),
    "boot-fill": makeElement("boot-fill"),
    "boot-status": makeElement("boot-status"),
  };
  const body = makeElement("body");
  const mediaListeners = [];
  const state = { portrait };

  const timers = [];
  const ctx = {
    console: { log: () => {}, info: () => {}, warn: () => {}, error: () => {} },
    JSON, Math, String, Boolean, Number, Object, Array, Promise, Error,
    setTimeout: (fn, ms) => { timers.push({ fn, ms }); return timers.length; },
    navigator: { language: "ru-RU", maxTouchPoints: touch ? 5 : 0 },
    document: {
      documentElement: {}, title: "", body,
      querySelectorAll: () => i18nNodes,
      getElementById: (id) => byId[id] ?? makeElement(id),
      addEventListener: () => {},
    },
    Engine: class Engine {
      static getMissingFeatures() { return missingFeatures; }
      constructor(cfg) { this.cfg = cfg; }
      startGame({ onProgress }) {
        onProgress(50, 100);
        return startFails ? Promise.reject(new Error("boom")) : Promise.resolve();
      }
    },
    _log: log, _timers: timers, _state: state,
  };
  ctx.window = {
    addEventListener: () => {},
    setTimeout: ctx.setTimeout,
    matchMedia: (q) => ({
      matches: q.includes("orientation: portrait") ? state.portrait
             : q.includes("pointer: coarse") ? touch : false,
      addEventListener: (_n, fn) => mediaListeners.push(fn),
    }),
  };
  ctx.globalThis = ctx;
  if (withSdk) {
    ctx.YaGames = {
      init: () => Promise.resolve({
        environment: { i18n: { lang: "en" } },
        deviceInfo: { type: "mobile" },
        features: {
          LoadingAPI: { ready: () => log.push(["call", "LoadingAPI.ready"]) },
          GameplayAPI: {
            start: () => log.push(["call", "GameplayAPI.start"]),
            stop: () => log.push(["call", "GameplayAPI.stop"]),
          },
        },
        adv: {
          showFullscreenAdv: ({ callbacks }) => {
            log.push(["call", "showFullscreenAdv"]);
            callbacks.onOpen();
            callbacks.onClose();
          },
        },
        on: (name, fn) => { (ctx._sdkEvents ??= {})[name] = fn; },
        getPlayer: () => Promise.resolve({
          getData: (keys) => { log.push(["call", "player.getData:" + keys]); return Promise.resolve({ palata0: { selected_night: 3 } }); },
          setData: (obj, flush) => { log.push(["call", "player.setData", JSON.stringify(obj), flush]); return Promise.resolve(); },
        }),
      }),
    };
  }
  vm.createContext(ctx);
  return { ctx, log, mediaListeners, body };
}

const results = [];
function check(name, ok, detail = "") {
  results.push({ name, ok, detail });
}

// --- case 1: real SDK, mobile, events buffered until Godot connects ----------
{
  const { ctx, log, body, mediaListeners } = buildContext({ withSdk: true, touch: true, portrait: false });
  vm.runInContext(source, ctx);
  check("body marked mobile-device", body.classList.contains("mobile-device"));
  await new Promise((r) => setImmediate(r));
  await new Promise((r) => setImmediate(r));
  await new Promise((r) => setImmediate(r));

  // Godot connects LATE, after the SDK already resolved.
  const seen = [];
  ctx.window.YandexGamesBridge.connectGodot((name, payload) => seen.push([name, payload]));
  const names = seen.map((e) => e[0]);
  check("sdk_ready buffered and replayed", names[0] === "sdk_ready", JSON.stringify(names));
  check("cloud_data replayed after sdk_ready", names.includes("cloud_data"), JSON.stringify(names));
  const ready = JSON.parse(seen.find((e) => e[0] === "sdk_ready")[1]);
  check("sdk_ready carries language", ready.language === "en", JSON.stringify(ready));
  check("sdk_ready carries device_type", ready.device_type === "mobile", JSON.stringify(ready));
  const cloud = JSON.parse(seen.find((e) => e[0] === "cloud_data")[1]);
  check("cloud_data unwraps the palata0 key", cloud.selected_night === 3, JSON.stringify(cloud));

  seen.length = 0;
  ctx.window.YandexGamesBridge.loadingReady();
  check("loadingReady hits LoadingAPI", log.some((e) => e[1] === "LoadingAPI.ready"));
  ctx.window.YandexGamesBridge.setGameplayActive(true);
  check("setGameplayActive(true) starts GameplayAPI", log.some((e) => e[1] === "GameplayAPI.start"));
  ctx.window.YandexGamesBridge.setGameplayActive(false);
  check("setGameplayActive(false) stops GameplayAPI", log.some((e) => e[1] === "GameplayAPI.stop"));

  ctx.window.YandexGamesBridge.showInterstitial();
  check("interstitial emits ad_open then ad_close",
    JSON.stringify(seen.map((e) => e[0])) === JSON.stringify(["ad_open", "ad_close"]),
    JSON.stringify(seen.map((e) => e[0])));

  ctx.window.YandexGamesBridge.saveData(JSON.stringify({ selected_night: 7 }), true);
  const save = log.find((e) => e[1] === "player.setData");
  check("saveData wraps progress in the palata0 key", save && JSON.parse(save[2]).palata0.selected_night === 7, JSON.stringify(save));
  check("saveData forwards the cloud flush flag", save && save[3] === true);

  ctx._sdkEvents.game_api_pause();
  ctx._sdkEvents.game_api_resume();
  check("platform pause/resume forwarded",
    seen.some((e) => e[0] === "platform_pause") && seen.some((e) => e[0] === "platform_resume"));

  seen.length = 0;
  ctx._state.portrait = true;
  mediaListeners.forEach((fn) => fn());
  check("portrait pauses the shift", seen.some((e) => e[0] === "platform_pause"), JSON.stringify(seen));
  seen.length = 0;
  ctx._state.portrait = false;
  mediaListeners.forEach((fn) => fn());
  check("landscape resumes it", seen.some((e) => e[0] === "platform_resume"), JSON.stringify(seen));
}

// --- case 2: no SDK (local run) --------------------------------------------
{
  const { ctx } = buildContext({ withSdk: false, touch: false, portrait: false });
  vm.runInContext(source, ctx);
  const seen = [];
  ctx.window.YandexGamesBridge.connectGodot((n, p) => seen.push([n, p]));
  check("standalone run reports sdk_unavailable", seen.some((e) => e[0] === "sdk_unavailable"), JSON.stringify(seen));
  seen.length = 0;
  ctx.window.YandexGamesBridge.showInterstitial();
  check("ad without SDK still releases the game", seen.length === 1 && seen[0][0] === "ad_close", JSON.stringify(seen));
  ctx.window.YandexGamesBridge.saveData("{}", true);
  check("saveData without a player does not throw", true);
  ctx.window.YandexGamesBridge.loadingReady();
  check("loadingReady without SDK does not throw", true);
}

// --- case 3: SDK init times out ---------------------------------------------
{
  const { ctx } = buildContext({ withSdk: true, touch: true, portrait: false });
  ctx.YaGames.init = () => new Promise(() => {});
  vm.runInContext(source, ctx);
  const seen = [];
  ctx.window.YandexGamesBridge.connectGodot((n, p) => seen.push([n, p]));
  const timer = ctx._timers.find((t) => t.ms === 10000);
  check("a 10 s init watchdog is armed", Boolean(timer));
  timer.fn();
  check("watchdog reports sdk_unavailable", seen.some((e) => e[0] === "sdk_unavailable"), JSON.stringify(seen));
}

// --- case 4: browser missing WebGL2 etc. ------------------------------------
{
  const { ctx } = buildContext({ withSdk: true, touch: false, portrait: false, missingFeatures: ["WebGL2"] });
  vm.runInContext(source, ctx);
  const seen = [];
  ctx.window.YandexGamesBridge.connectGodot((n, p) => seen.push([n, p]));
  check("unsupported browser releases the loading screen", seen.some((e) => e[0] === "sdk_unavailable"), JSON.stringify(seen));
}

const failed = results.filter((r) => !r.ok);
for (const r of results) console.log((r.ok ? "  ok   " : "  FAIL ") + r.name + (r.ok ? "" : "  <- " + r.detail));
console.log("\nSHELL_CHECK checks=" + results.length + " failures=" + failed.length);
process.exit(failed.length ? 1 : 0);
