// Render video/src/scenes.html to an MP4, frame by frame.
//
//   node render.mjs                      full video -> ../compostito-explainer.mp4 (+ .srt, .vtt)
//   node render.mjs --stills 12,30,55    PNG stills at those times -> ./stills/
//
// Needs playwright-core, ffmpeg on PATH, and a Chromium build. Set CHROMIUM to
// its executable if it isn't the Playwright default.
import { chromium } from "playwright-core";
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, "..");
const FPS = 30;
const args = process.argv.slice(2);
const stillsArg = args.includes("--stills") ? args[args.indexOf("--stills") + 1] : null;

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(join(here, "scenes.html")).href);
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.DURATION);
const stage = await page.$("#stage");

if (stillsArg) {
  mkdirSync(join(here, "stills"), { recursive: true });
  for (const t of stillsArg.split(",").map(Number)) {
    await page.evaluate(t => window.renderFrame(t), t);
    await stage.screenshot({ path: join(here, "stills", `t${String(t).padStart(6, "0")}.png`) });
  }
  await browser.close();
  process.exit(0);
}

// captions
const caps = await page.evaluate(() => window.CAPTIONS);
const ts = (s, sep) => {
  const ms = Math.round(s * 1000), h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, sec = Math.floor(ms / 1000) % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}${sep}${String(ms % 1000).padStart(3, "0")}`;
};
const plain = h => h.replace(/<[^>]+>/g, "");
writeFileSync(join(out, "compostito-explainer.srt"),
  caps.map((c, i) => `${i + 1}\n${ts(c.start, ",")} --> ${ts(c.end, ",")}\n${plain(c.html)}\n`).join("\n"));
writeFileSync(join(out, "compostito-explainer.vtt"),
  "WEBVTT\n\n" + caps.map(c => `${ts(c.start, ".")} --> ${ts(c.end, ".")}\n${plain(c.html)}\n`).join("\n"));

const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
  "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-vf", "scale=in_range=full:out_range=tv,format=yuv420p", "-color_range", "tv", "-movflags", "+faststart",
  join(out, "compostito-explainer.mp4")], { stdio: ["pipe", "inherit", "inherit"] });
const n = Math.round(duration * FPS);
for (let i = 0; i < n; i++) {
  await page.evaluate(t => window.renderFrame(t), i / FPS);
  const buf = await stage.screenshot({ type: "jpeg", quality: 95 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  if (i % 300 === 0) console.log(`frame ${i}/${n}`);
}
ff.stdin.end();
await new Promise(r => ff.on("close", r));
// poster: a frame from the Compostito chapter
await page.evaluate(() => window.renderFrame(window.CHAPTERS.find(c => c.id === "c3").start + 14));
await stage.screenshot({ path: join(out, "poster.png") });
await browser.close();
console.log(`done: ${n} frames, ${duration.toFixed(1)} s`);
