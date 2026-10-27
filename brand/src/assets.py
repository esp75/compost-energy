"""Generate every brand asset in the manifest (04_manifest/manifest.md).

    .venv/bin/python brand/src/assets.py

SVGs are written directly; PNGs are rendered from SVG or HTML with
brand/src/render.mjs (headless Chrome). Imagery is procedural: particle
rings and contour fields drawn on a canvas, plus the supplied ring.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import mark  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
BUILD = ROOT / "src" / "build"
FONTS = ROOT / "11_typography" / "fonts"
PRIMARY = ROOT / "05_logo_primary"
VAR = ROOT / "06_logo_variants"
MKT = ROOT / "09_marketing"

TAGLINE = "Heat from what farms already make."
SUB = "Open-hardware compost heat recovery. Every number is in the repo."


def render(src: Path, out: Path, w: int, h: int, scale: int = 1) -> None:
    subprocess.run(["node", str(ROOT / "src" / "render.mjs"), str(src), str(out), str(w), str(h), str(scale)],
                   check=True, cwd=REPO, stdout=subprocess.DEVNULL)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


# ---------------------------------------------------------------------------
# HTML templates for raster marketing assets
# ---------------------------------------------------------------------------

def page(w: int, h: int, body: str, light: bool = False, field: str = "ring") -> str:
    bg = "#e3eae5" if light else "#060a07"
    ink = "#0f1a13" if light else "#eef3ef"
    muted = "#4a5c51" if light else "#93a69a"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: "Instrument Sans"; src: url("{FONTS / 'InstrumentSans.ttf'}"); font-weight: 400 700; }}
@font-face {{ font-family: "Geist Mono"; src: url("{FONTS / 'GeistMono.ttf'}"); font-weight: 100 900; }}
* {{ box-sizing: border-box; margin: 0; }}
html, body {{ width: {w}px; height: {h}px; overflow: hidden; background: {bg}; color: {ink};
  font-family: "Instrument Sans", sans-serif; }}
canvas {{ position: absolute; inset: 0; }}
.label {{ font: 500 {max(12, w // 110)}px "Geist Mono", monospace; letter-spacing: .14em; text-transform: uppercase; color: {muted}; }}
.muted {{ color: {muted}; }}
.abs {{ position: absolute; }}
</style></head><body>
<canvas id="c" width="{w}" height="{h}"></canvas>
{body}
<script>
const c = document.getElementById("c"), x = c.getContext("2d"), W = {w}, H = {h}, LIGHT = {str(light).lower()};
let s = 7; const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
const leaf = LIGHT ? "61,110,34" : "124,192,74", ember = LIGHT ? "178,63,10" : "242,106,33";
function contours(y0, amp, n, alpha) {{
  x.lineWidth = Math.max(0.6, W / 2400);
  for (let i = 0; i < n; i++) {{
    const t = i / n;
    x.strokeStyle = `rgba(${{t < .5 ? leaf : ember}},${{alpha * (0.35 + 0.65 * Math.sin(t * Math.PI))}})`;
    x.beginPath();
    for (let X = 0; X <= W; X += 6) {{
      const Y = y0 + i * (H * 0.0045) + amp * Math.sin(X / (W / 6) + i / 13) + amp * 0.5 * Math.sin(X / (W / 17) - i / 8) * (X / W);
      X ? x.lineTo(X, Y) : x.moveTo(X, Y);
    }}
    x.stroke();
  }}
}}
function particles(cx, cy, R, n, warmRight) {{
  for (let i = 0; i < n; i++) {{
    const a = r() * Math.PI * 2, rad = R * (1 + (r() - 0.4) * 0.55 * r());
    const px = cx + Math.cos(a) * rad, py = cy + Math.sin(a) * rad;
    const hot = warmRight ? Math.cos(a) > -0.15 : r() > .5;
    x.fillStyle = `rgba(${{hot ? ember : leaf}},${{0.15 + r() * 0.6}})`;
    x.beginPath(); x.arc(px, py, (0.4 + r() * r() * 1.8) * Math.max(1, W / 1600), 0, 7); x.fill();
  }}
}}
{field}
</script></body></html>"""


def ring_img(css: str, light=False) -> str:
    f = PRIMARY / ("mark_v2_light.png" if light else "mark_v2_dark.png")
    return f'<img class="abs" src="{f}" style="{css}">'


def svg_img(path: Path, css: str) -> str:
    return f'<img class="abs" src="{path}" style="{css}">'


def build_marketing(word_dark: Path, word_light: Path) -> list[Path]:
    out = []

    # GitHub social preview 1280x640 (dark)
    html = page(1280, 640, f"""
{ring_img("left:60px;top:105px;width:520px")}
{svg_img(word_dark, "left:600px;top:200px;width:620px")}
<div class="abs" style="left:640px;top:330px;width:560px;font:500 30px/1.2 'Instrument Sans';letter-spacing:-.01em">{TAGLINE}</div>
<div class="abs label" style="left:640px;top:420px">Open hardware · model · drawings · data</div>
<div class="abs label" style="left:640px;top:560px">CERN-OHL-P · MIT · CC-BY-4.0</div>""",
               field="particles(320, 320, 280, 380, true); contours(470, 26, 46, .10);")
    out.append(render_html(html, MKT / "github_social_1280x640.png", 1280, 640))

    # README banners 1600x480
    for light in (False, True):
        word = word_light if light else word_dark
        html = page(1600, 480, f"""
{ring_img("left:70px;top:40px;width:470px", light)}
{svg_img(word, "left:600px;top:118px;width:900px")}
<div class="abs" style="left:640px;top:300px;font:500 34px/1.2 'Instrument Sans';letter-spacing:-.015em">{TAGLINE}</div>
<div class="abs label" style="left:640px;top:362px">{SUB}</div>""",
                    light=light, field="contours(330, 22, 40, LIGHT ? .10 : .12);" + ("" if light else "particles(305, 235, 230, 260, true);"))
        name = "readme_banner_light.png" if light else "readme_banner_dark.png"
        out.append(render_html(html, MKT / name, 1600, 480))

    # OG card 1200x630
    html = page(1200, 630, f"""
{ring_img("right:-60px;top:40px;width:640px;opacity:.95")}
<div class="abs label" style="left:72px;top:72px">Compost Energy · research</div>
<div class="abs" style="left:72px;top:150px;width:620px;font:500 76px/1.0 'Instrument Sans';letter-spacing:-.035em">Heat from what farms already make.</div>
<div class="abs muted" style="left:72px;top:440px;width:520px;font:400 22px/1.45 'Instrument Sans'">{SUB}</div>
{svg_img(word_dark, "left:72px;top:540px;width:300px")}""",
               field="particles(860, 300, 290, 420, true); contours(420, 30, 50, .10);")
    out.append(render_html(html, MKT / "og_1200x630.png", 1200, 630))

    # Hero 1920x1080: procedural field + ring, no copy (pages set their own type)
    html = page(1920, 1080, ring_img("left:1010px;top:150px;width:900px"),
                field="contours(560, 60, 90, .14); particles(1460, 520, 430, 1400, true);")
    out.append(render_html(html, MKT / "hero_16x9.png", 1920, 1080))

    # Video title + end cards 1920x1080
    html = page(1920, 1080, f"""
{ring_img("left:560px;top:110px;width:800px")}
{svg_img(word_dark, "left:360px;top:760px;width:1200px")}""",
                field="particles(960, 420, 360, 900, true);")
    out.append(render_html(html, MKT / "video_title.png", 1920, 1080))
    html = page(1920, 1080, f"""
{ring_img("left:140px;top:300px;width:560px")}
<div class="abs label" style="left:800px;top:330px">Compost Energy</div>
<div class="abs" style="left:800px;top:380px;width:980px;font:500 72px/1.05 'Instrument Sans';letter-spacing:-.03em">Nothing at this scale has been built yet.</div>
<div class="abs muted" style="left:800px;top:580px;width:900px;font:400 28px/1.5 'Instrument Sans'">Every number in this film comes from the open model. Measured values are labelled MEASURED; everything else is MODEL.</div>
{svg_img(word_dark, "left:800px;top:800px;width:520px")}""",
                field="contours(780, 34, 60, .10); particles(420, 540, 300, 500, true);")
    out.append(render_html(html, MKT / "video_end.png", 1920, 1080))
    return out


def render_html(html: str, out: Path, w: int, h: int) -> Path:
    src = write(BUILD / (out.stem + ".html"), html)
    out.parent.mkdir(parents=True, exist_ok=True)
    render(src, out, w, h)
    return out


# ---------------------------------------------------------------------------

def build_logos() -> dict:
    VAR.mkdir(exist_ok=True)
    files = {}
    for light in (False, True):
        tag = "light" if light else "dark"
        files[f"horizontal_{tag}"] = write(VAR / f"horizontal_{tag}.svg", mark.horizontal(light=light))
        render(files[f"horizontal_{tag}"], VAR / f"horizontal_{tag}.png", 1600, 400)
        files[f"stacked_{tag}_t"] = write(VAR / f"stacked_{tag}_transparent.svg", mark.stacked(light=light, bg=False))
        files[f"wordmark_{tag}"] = write(VAR / f"wordmark_{tag}.svg", mark.wordmark_only(light=light))
        render(files[f"wordmark_{tag}"], VAR / f"wordmark_{tag}.png", 1600, 260)
        write(VAR / f"mark_mono_{tag}.svg", mark.mark_only("mono", light=light, size=512))
    shutil.copy(PRIMARY / "mark_v2_dark.png", VAR / "mark_ring_dark.png")
    shutil.copy(PRIMARY / "mark_v2_light.png", VAR / "mark_ring_light.png")
    flat = write(VAR / "favicon.svg", mark.mark_only("flat", size=64))
    big_flat = write(BUILD / "favicon_512.svg", mark.mark_only("flat", size=512))
    render(big_flat, BUILD / "favicon_512.png", 512, 512)    # Chrome won't screenshot a 16 px viewport
    from PIL import Image
    for n in (16, 32):
        Image.open(BUILD / "favicon_512.png").resize((n, n), Image.LANCZOS).save(VAR / f"favicon-{n}.png")
    # app icon: the ring on a Night tile
    tile = page(512, 512, ring_img("left:36px;top:70px;width:440px"), field="")
    render_html(tile, VAR / "app_icon_512.png", 512, 512)
    from PIL import Image
    big = Image.open(VAR / "app_icon_512.png")
    big.resize((180, 180), Image.LANCZOS).save(VAR / "apple-touch-icon.png")
    big.resize((48, 48), Image.LANCZOS).save(VAR / "favicon-48.png")
    write(MKT / "drawing_titleblock_mark.svg", mark.mark_only("flat", size=64))
    return files


def build_palette() -> None:
    import json
    t = json.loads((ROOT / "10_color" / "tokens.json").read_text())
    sw = lambda c, label, ink: (f'<div style="flex:1;border-radius:28px;padding:22px;background:{c};color:{ink};'  # noqa: E731
                                f'display:flex;flex-direction:column;justify-content:space-between;border:1px solid rgba(128,128,128,.25)">'
                                f'<b style="font:500 20px Instrument Sans">{label}</b><span style="font:14px Geist Mono">{c}</span></div>')
    d, l = t["dark"], t["light"]
    body = f"""<div class="abs" style="inset:60px 70px;display:flex;flex-direction:column;gap:26px">
<div class="label">Compost Energy · colour · leaf = matter · ember = heat</div>
<div style="display:flex;gap:18px;height:300px">{sw(d['bg'], 'Night', d['text'])}{sw(d['surface'], 'Night surface', d['text'])}{sw(d['leaf'], 'Leaf', d['bg'])}{sw(d['ember'], 'Ember', d['bg'])}{sw(d['glow'], 'Glow', d['bg'])}</div>
<div style="display:flex;gap:18px;height:300px">{sw(l['bg'], 'Mist', l['text'])}{sw(l['surface'], 'Mist surface', l['text'])}{sw(l['text'], 'Moss ink', l['bg'])}{sw(l['leaf'], 'Leaf (light)', l['bg'])}{sw(l['ember'], 'Ember (light)', l['bg'])}</div>
</div>"""
    render_html(page(1600, 820, body, field=""), ROOT / "10_color" / "palette_v1.png", 1600, 820)


if __name__ == "__main__":
    BUILD.mkdir(parents=True, exist_ok=True)
    files = build_logos()
    build_marketing(files["wordmark_dark"], files["wordmark_light"])
    build_palette()
    # the specimen page doubles as the typography specimen
    render(ROOT / "src" / "specimen.html", ROOT / "11_typography" / "specimen.png", 1600, 3700)
    print("done")
