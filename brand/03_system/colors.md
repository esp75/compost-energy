# Colour system

Sampled from the logo reference (leaf `#3c6623`/`#e9f07e`, ember `#e14c03`/`#800900`) and from moods 3–5 (moss `#2a3c32`, sage `#b2c6b9`, grey `#c3cfda`). Two grounds, one meaning: **leaf = organic matter and process, ember = heat and energy.** Ember is never decoration.

## Dark (Night) — hero, video, dark mode

| Token | Hex | Role | Contrast on bg / surface |
|---|---|---|---|
| `bg` | `#060a07` | Night ground, green-tinted black | — |
| `surface` | `#0e1611` | Glass cards (used at 70 % with blur) | — |
| `text` | `#eef3ef` | Body and headlines | 17.7 / 16.4 |
| `text-muted` | `#93a69a` | Captions, labels | 7.7 / 7.2 |
| `leaf` (accent-1) | `#7cc04a` | Matter, process, links | 9.0 / 8.3 |
| `ember` (accent-2) | `#f26a21` | Heat, energy figures | 6.5 / 6.0 |
| `glow` | `#e9f07e` | Particle highlights, the leaf tip (no text) | — |

## Light (Mist) — reading pages, drawings, README

| Token | Hex | Role | Contrast on bg / surface |
|---|---|---|---|
| `bg` | `#e3eae5` | Mist ground | — |
| `surface` | `#f4f7f5` | Glass cards (used at 75 % with blur) | — |
| `text` | `#0f1a13` | Moss ink | 14.6 / 16.5 |
| `text-muted` | `#4a5c51` | Captions, labels | 5.8 / 6.6 |
| `leaf` (accent-1) | `#3d6e22` | Matter, process, links | 5.0 / 5.6 |
| `ember` (accent-2) | `#b23f0a` | Heat, energy figures | 4.8 / 5.4 |

All text pairs pass WCAG AA for body text (≥ 4.5:1). Computed with the WCAG 2.1 relative-luminance formula.

## Gradient (mark only)

`leaf #6fae3c → #a7b83f → #e0882a → ember #f26a21 → #b5300a`, along the band. Gradients appear only on the mark and in heat-map data, never as backgrounds.

## Data ramp (charts, drawings)

Cold → hot: `#2f6f73` (water, cold side) · `#3d6e22` · `#a7b83f` · `#e0882a` · `#b23f0a`. Phases in drawings: heat-up `#a7b83f`, hot `#e0882a`, cooling `#6f9fa0`, maturation `#7a8f6a`.
