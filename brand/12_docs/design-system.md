# Compost Energy — design system (for coding agents)

## 1. Brand context
Open-hardware compost heat recovery. Two grounds: **Night** (hero, video, dark mode) and **Mist** (reading, drawings, light mode). Leaf green = organic matter / process. Ember orange = heat / energy. Tone: precise, calm, candid; every figure tagged MODEL / SIMULATED / MEASURED.

## 2. CSS custom properties
```css
:root {
  --ce-bg: #e3eae5; --ce-surface: #f4f7f5; --ce-text: #0f1a13; --ce-muted: #4a5c51;
  --ce-leaf: #3d6e22; --ce-ember: #b23f0a; --ce-hairline: rgba(15, 26, 19, 0.14);
  --ce-glass: rgba(244, 247, 245, 0.75); --ce-glass-edge: rgba(255, 255, 255, 0.7);
  --ce-glow: #e9f07e;
  --ce-radius-sm: 8px; --ce-radius-card: 28px; --ce-radius-full: 9999px;
  --ce-ease: cubic-bezier(0.22, 1, 0.36, 1);
  --ce-font-text: "Instrument Sans", system-ui, sans-serif;
  --ce-font-mono: "Geist Mono", ui-monospace, monospace;
  --ce-font-figure: "Unbounded", "Instrument Sans", sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ce-bg: #060a07; --ce-surface: #0e1611; --ce-text: #eef3ef; --ce-muted: #93a69a;
    --ce-leaf: #7cc04a; --ce-ember: #f26a21; --ce-hairline: rgba(238, 243, 239, 0.14);
    --ce-glass: rgba(14, 22, 17, 0.62); --ce-glass-edge: rgba(238, 243, 239, 0.14);
  }
}
:root[data-theme="dark"] {
  --ce-bg: #060a07; --ce-surface: #0e1611; --ce-text: #eef3ef; --ce-muted: #93a69a;
  --ce-leaf: #7cc04a; --ce-ember: #f26a21; --ce-hairline: rgba(238, 243, 239, 0.14);
  --ce-glass: rgba(14, 22, 17, 0.62); --ce-glass-edge: rgba(238, 243, 239, 0.14);
}
```

## 3. Type scale
```css
.ce-display { font: 500 clamp(3rem, 8vw, 7.5rem)/0.98 var(--ce-font-text); letter-spacing: -0.035em; }
.ce-h1 { font: 500 clamp(2.25rem, 5vw, 4rem)/1.02 var(--ce-font-text); letter-spacing: -0.03em; }
.ce-h2 { font: 500 clamp(1.6rem, 3vw, 2.5rem)/1.1 var(--ce-font-text); letter-spacing: -0.02em; }
.ce-h3 { font: 600 1.25rem/1.3 var(--ce-font-text); letter-spacing: -0.01em; }
.ce-figure { font: 600 clamp(2rem, 4vw, 3.5rem)/1 var(--ce-font-figure); letter-spacing: -0.02em; color: var(--ce-ember); }
.ce-body { font: 400 1.0625rem/1.6 var(--ce-font-text); }
.ce-small { font: 400 0.875rem/1.5 var(--ce-font-text); }
.ce-label { font: 500 0.75rem/1.4 var(--ce-font-mono); letter-spacing: 0.12em; text-transform: uppercase; color: var(--ce-muted); }
```

## 4. Component patterns
- **Glass card:** `background: var(--ce-glass); backdrop-filter: blur(18px); border: 1px solid var(--ce-glass-edge); border-radius: var(--ce-radius-card); padding: clamp(24px, 4vw, 40px);` No shadow.
- **Notched card:** add a 44 × 88 px half-circle cut on one edge (`mask` or an absolutely positioned element in the ground colour) holding a ring icon or a progress rail.
- **Figure block:** `.ce-label` (what) → `.ce-figure` (number + unit) → `.ce-label` (MODEL / SIMULATED / MEASURED + source).
- **Button:** pill, 1 px `currentColor` border, label + trailing arrow in its own circle; hover fills with `--ce-text` at 8 %.
- **Section marker:** `01 · Title` in `.ce-label`, then an h2.
- **Figure/drawing frame:** radius 28 px, hairline border, caption below in `.ce-small` with the source tag.
- **Tag chips:** Geist Mono, radius 8 px, hairline border: `T-101`, `CE-12`.

## 5. Animation
- Entrances: opacity 0 → 1 and translateY(16px) → 0, 700 ms, `var(--ce-ease)`, stagger 60 ms. Respect `prefers-reduced-motion`.
- Ring: optional slow rotation (≥ 60 s per turn) or a leaf → ember colour sweep. Never scale-bounce.
- Particles: drift upward at 4–12 px/s on the heat side; hide when `prefers-reduced-motion`.

## 6. Layout
- Max text width 68ch; page max 1200 px; side gutter 16 px (phone) → 72 px (desktop).
- Vertical rhythm: sections `padding-block: clamp(72px, 12vw, 160px)`.
- Grid: 12 columns, 24 px gap; headlines span 7–8, figures and cards on the right 4–5.
- Hero: Night ground, ring right, headline left, contour texture behind at ≤ 25 %.

## 7. Anti-patterns
1. Inter, Roboto, Poppins, Montserrat, Open Sans.
2. Drop shadows, `box-shadow` on cards.
3. 1 px grey borders on everything; use hairlines only where structure needs them.
4. Ember used for buttons or decoration.
5. Glow or particles on Mist.
6. Gradients as backgrounds (gradients live only in the mark and in heat data).
7. Globe, planet, turbine, lightbulb or upward-arrow imagery.
8. Unlabelled numbers.
9. `ease-in-out` defaults, bouncy springs.
10. Re-typesetting the logo in a font.
11. Pure black `#000` or pure white `#fff` grounds.
12. All-caps body text.

## 8. Tailwind config
```js
export default {
  theme: {
    extend: {
      colors: {
        night: { DEFAULT: "#060a07", surface: "#0e1611", text: "#eef3ef", muted: "#93a69a" },
        mist: { DEFAULT: "#e3eae5", surface: "#f4f7f5", text: "#0f1a13", muted: "#4a5c51" },
        leaf: { DEFAULT: "#3d6e22", bright: "#7cc04a" },
        ember: { DEFAULT: "#b23f0a", bright: "#f26a21" },
        glow: "#e9f07e",
      },
      fontFamily: {
        sans: ["Instrument Sans", "system-ui", "sans-serif"],
        mono: ["Geist Mono", "ui-monospace", "monospace"],
        figure: ["Unbounded", "Instrument Sans", "sans-serif"],
      },
      borderRadius: { card: "28px" },
      transitionTimingFunction: { brand: "cubic-bezier(0.22, 1, 0.36, 1)" },
    },
  },
};
```

## 9. Google Fonts import
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&family=Geist+Mono:wght@400;500&family=Unbounded:wght@600&display=swap" rel="stylesheet">
```

## Other targets
- **matplotlib** (`model/compost_energy/plotting.py`): ink `#0f1a13`, muted `#4a5c51`, grid `rgba(15,26,19,0.12)` → `#d3dbd6`, background `#e3eae5` or transparent, hot `#b23f0a`, cool `#2f6f73`, leaf `#3d6e22`; phases as in Brand-Booklet §4.
- **SVG drawings** (`hardware/drawings/src/make_drawings.py` PALETTES): light = Mist tokens, dark = Night tokens; phase fills from the data colours; text in Geist Mono with `Menlo, monospace` fallback.
