// Render video/src/demo.html (the farm-scale unit product demo) to an MP4.
//
//   node render-demo.mjs                    full video -> ../farm-unit-demo.mp4 (+ .srt, .vtt, poster)
//   node render-demo.mjs --stills 5,30,55   PNG stills at those times -> ./stills/
//
// The page loads three.js and the CAD export over HTTP, so this script serves
// the repository root on a local port while it renders. Needs playwright-core,
// ffmpeg on PATH and Chrome or Chromium (set CHROMIUM to its executable).
// Run `python hardware/cad/farm_unit.py` first to build the model files.
import { chromium } from "playwright-core";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..", "..");
const out = join(here, "..");
const FPS = 30;
const args = process.argv.slice(2);
const stillsArg = args.includes("--stills") ? args[args.indexOf("--stills") + 1] : null;
const MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json", ".glb": "model/gltf-binary" };
const server = createServer((req, res) => {
  const path = normalize(join(root, decodeURIComponent(new URL(req.url, "http://x").pathname)));
  if (!path.startsWith(root) || !existsSync(path)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": TYPES[extname(path)] || "application/octet-stream" });
  res.end(readFileSync(path));
});
await new Promise(r => server.listen(0, "127.0.0.1", r));
const base = `http://127.0.0.1:${server.address().port}`;

const executablePath = process.env.CHROMIUM || (existsSync(MAC_CHROME) ? MAC_CHROME : undefined);
const browser = await chromium.launch({ executablePath, args: ["--use-angle=metal", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on("pageerror", e => console.error("page error:", e.message));
await page.goto(`${base}/video/src/demo.html`);
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.DURATION);
const stage = await page.$("#stage");

async function frame(t) { await page.evaluate(t => window.renderFrame(t), t); }

if (stillsArg) {
  mkdirSync(join(here, "stills"), { recursive: true });
  for (const t of stillsArg.split(",").map(Number)) {
    await frame(t);
    await stage.screenshot({ path: join(here, "stills", `demo-t${String(t).padStart(5, "0")}.png`) });
  }
} else {
  const caps = await page.evaluate(() => window.CAPTIONS);
  const ts = (s, sep) => {
    const ms = Math.round(s * 1000), h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, sec = Math.floor(ms / 1000) % 60;
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}${sep}${String(ms % 1000).padStart(3, "0")}`;
  };
  const plain = h => h.replace(/<[^>]+>/g, "");
  writeFileSync(join(out, "farm-unit-demo.srt"),
    caps.map((c, i) => `${i + 1}\n${ts(c.start, ",")} --> ${ts(c.end, ",")}\n${plain(c.html)}\n`).join("\n"));
  writeFileSync(join(out, "farm-unit-demo.vtt"),
    "WEBVTT\n\n" + caps.map(c => `${ts(c.start, ".")} --> ${ts(c.end, ".")}\n${plain(c.html)}\n`).join("\n"));

  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-vf", "scale=in_range=full:out_range=tv,format=yuv420p", "-color_range", "tv",
    "-movflags", "+faststart", join(out, "farm-unit-demo.mp4")], { stdio: ["pipe", "inherit", "inherit"] });
  const n = Math.round(duration * FPS);
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await frame(i / FPS);
    const buf = await stage.screenshot({ type: "jpeg", quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if (i % 300 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  await frame(56);
  await stage.screenshot({ path: join(out, "farm-unit-demo-poster.png") });
  console.log(`done: ${n} frames, ${duration.toFixed(1)} s`);
}
await browser.close();
server.close();
