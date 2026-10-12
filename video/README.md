# Explainer video: how Compostito works

| File | What |
|---|---|
| [`compostito-explainer.mp4`](compostito-explainer.mp4) | 1920 × 1080, 30 fps, about 2 min 40 s, H.264. Captions are burned in; there is no audio. |
| [`compostito-explainer.srt`](compostito-explainer.srt) / [`.vtt`](compostito-explainer.vtt) | The same captions as subtitle files |
| [`narration-script.md`](narration-script.md) | Timed script, for recording a voiceover later |
| [`poster.png`](poster.png) | Thumbnail frame |

Chapters: what compost is · aerobic vs anaerobic · meet Compostito · microbes make heat · the four phases · from heat to the farm · a better fertiliser.

**What the numbers are:**

- The temperature curves are **simulated**, from [`data/simulated/truth_run_01.csv`](../data/simulated/truth_run_01.csv), and they're labelled that way on screen.
- The 38% farm heat recovery is a **third-party measurement** (Kojima et al., 2022), credited on screen.
- The 50 W pipe and the 99.5% resistance share come from the [exchanger model](../model/compost_energy/heat_exchanger.py).
- The methane factor is the IPCC AR5 100-year figure.

## Rebuild

The video is rendered from code. [`src/scenes.html`](src/scenes.html) draws each frame as a pure function of time, Playwright screenshots it, and ffmpeg encodes the frames.

```bash
cd video/src
npm install playwright-core      # once; needs ffmpeg on PATH and a Chromium build
node render.mjs --stills 20,60   # preview frames into src/stills/
node render.mjs                  # full render: mp4, srt, vtt, poster
```

Set `CHROMIUM=/path/to/chrome` if Playwright's default browser isn't installed. To preview interactively, open `src/scenes.html?t=60` in a browser. Fonts are Instrument Serif and Inter Tight, loaded from Google Fonts.

Media is CC-BY-4.0 and `src/` is MIT (see [LICENSE.md](../LICENSE.md)).
