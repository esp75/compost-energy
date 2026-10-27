# Videos

## Farm-scale unit: product demo (98 s)

| File | What |
|---|---|
| `farm-unit-demo.mp4` | 1920 × 1080, 30 fps, H.264, captions burned in, no audio. Too large for git: download it from the GitHub release. |
| [`farm-unit-demo.srt`](farm-unit-demo.srt) / [`.vtt`](farm-unit-demo.vtt) | Captions |
| [`farm-unit-demo-poster.png`](farm-unit-demo-poster.png) | Thumbnail frame |

Chapters: tunnels · aeration · exhaust · heat recovery · operation (staggered batches) · control · numbers.

The scene is three.js, and it loads the CAD export [`hardware/cad/out/farm-unit.glb`](../hardware/cad/out/). Every number on screen is read from [`farm-unit.json`](../hardware/cad/out/farm-unit.json), which the CAD script writes from the sizing model, and each number is tagged MODEL or MEASURED. The closing card says that nothing at this scale has been built.

```bash
.venv/bin/python hardware/cad/farm_unit.py     # model files the scene loads
cd video/src && npm install
node render-demo.mjs --stills 15,40,70         # preview frames into src/stills/
node render-demo.mjs                           # full render (about 5 min on an M-series Mac)
```

`render-demo.mjs` serves the repository on a local port, since the page loads ES modules and the GLB over HTTP. It uses Google Chrome when it finds it; otherwise set `CHROMIUM`.

## Explainer: how compost makes heat

| File | What |
|---|---|
| [`compostito-explainer.mp4`](compostito-explainer.mp4) | 1920 × 1080, 30 fps, about 3 min 30 s, H.264. Captions are burned in; there is no audio. |
| [`compostito-explainer.srt`](compostito-explainer.srt) / [`.vtt`](compostito-explainer.vtt) | The same captions as subtitle files |
| [`narration-script.md`](narration-script.md) | Timed script, for recording a voiceover later |
| [`poster.png`](poster.png) | Thumbnail frame |

Chapters: what compost is · aerobic vs anaerobic · what the microbes need · microbes make heat · the four phases · where it started (Compostito) · the farm tunnel · heat and water · a better fertiliser.

**What the numbers are:**

- The pile temperature curves are **simulated**, from [`data/simulated/truth_run_01.csv`](../data/simulated/truth_run_01.csv), and they're labelled that way on screen.
- The farm-tunnel batch (temperature, phases, water per batch) is **MODEL**, from [`process.py`](../model/compost_energy/process.py). `run_process.py` writes it to [`src/tunnel-data.js`](src/tunnel-data.js). The other farm numbers (92 % latent, 330 kJ/kg, 2 GWh a year) come from [`farm-unit.json`](../hardware/cad/out/farm-unit.json).
- The process windows (C:N 25–35, moisture 50–60 %, O₂ at least 5 %, a pile of at least about 1 m³) are the on-farm composting handbook ranges in [`docs/process.md`](../docs/process.md).
- The 38% farm heat recovery is a **third-party measurement** (Kojima et al., 2022), credited on the end card.
- The 50 W pipe and the 99.5% resistance share come from the [exchanger model](../model/compost_energy/heat_exchanger.py).
- The methane factor is the IPCC AR5 100-year figure.

## Rebuild

The video is rendered from code. [`src/scenes.html`](src/scenes.html) draws each frame as a pure function of time, Playwright screenshots it, and ffmpeg encodes the frames.

```bash
cd video/src
npm install                      # once; needs ffmpeg on PATH and Chrome or Chromium
node render.mjs --stills 20,60   # preview frames into src/stills/
node render.mjs                  # full render: mp4, srt, vtt, poster
```

Set `CHROMIUM=/path/to/chrome` if Playwright's default browser isn't installed. To preview interactively, open `src/scenes.html?t=60` in a browser. Fonts are the brand's Instrument Sans, Unbounded and Geist Mono, loaded from Google Fonts; the logo comes from [`brand/`](../brand/).

Media is CC-BY-4.0 and `src/` is MIT (see [LICENSE.md](../LICENSE.md)).
