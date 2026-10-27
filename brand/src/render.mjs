// Rasterise brand HTML/SVG files to PNG (or PDF) with headless Chrome.
//
//   node brand/src/render.mjs <in.html|in.svg> <out.png> <width> <height> [scale]
//   node brand/src/render.mjs <in.html> <out.pdf> --pdf
//
// Reuses the playwright-core install in video/src (run `npm install` there first).

import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "../../video/src/node_modules/playwright-core/index.mjs";

const MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const executablePath = process.env.CHROMIUM || (existsSync(MAC_CHROME) ? MAC_CHROME : undefined);

const [input, output, a, b, c] = process.argv.slice(2);
if (!input || !output) {
  console.error("usage: render.mjs <in> <out> <width> <height> [scale] | <in> <out.pdf> --pdf");
  process.exit(1);
}

const browser = await chromium.launch({ executablePath });
const pdf = a === "--pdf";
const width = pdf ? 1240 : Number(a);
const height = pdf ? 1754 : Number(b);
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: pdf ? 1 : Number(c || 1) });
await page.goto(/^https?:/.test(input) ? input : pathToFileURL(resolve(input)).href, { waitUntil: "networkidle", timeout: 120000 });
await page.evaluate(() => document.fonts && document.fonts.ready);
await page.waitForTimeout(400);
if (pdf) {
  await page.emulateMedia({ media: "print" });
  await page.pdf({ path: output, format: "A4", printBackground: true, preferCSSPageSize: true,
                   margin: { top: "0", right: "0", bottom: "0", left: "0" } });
} else {
  await page.screenshot({ path: output, omitBackground: input.endsWith(".svg"), fullPage: process.env.FULL === "1" });
}
await browser.close();
console.log(output);
