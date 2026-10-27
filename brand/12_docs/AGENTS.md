# AGENTS.md — Compost Energy brand system

Entry point for any agent working with `brand/`. Read before touching assets.

## Quick reference

| Asset | Path | Status |
|---|---|---|
| Source logo artwork | `05_logo_primary/source_artwork.png` | LOCKED (Maxime's artwork) |
| Primary logo (dark / light) | `05_logo_primary/primary_v2.png`, `primary_v2_light.png` (+ .svg) | LOCKED |
| Ring cut-outs | `05_logo_primary/mark_v2_{dark,light}.png` | LOCKED (regenerate only via `src/extract_mark.py`) |
| Wordmark | `06_logo_variants/wordmark_{dark,light}.svg` | LOCKED |
| Colour tokens | `10_color/tokens.json` | REFERENCE |
| Typography spec | `11_typography/typography_spec.md` | REFERENCE |
| One-pager | `12_docs/Brand.md` | REFERENCE |
| Booklet | `12_docs/Brand-Booklet.md`, `13_booklet/booklet.pdf` | REFERENCE |
| Design tokens for code | `12_docs/design-system.md` | REFERENCE |

## Rules
- Never redraw or regenerate the ring. Use the cut-outs; at ≤ 32 px or one colour use `06_logo_variants/favicon.svg` / `mark_mono_*.svg`.
- No image models. All assets come from `src/` scripts (procedural) and the source artwork.
- Read `10_color/tokens.json` before choosing any colour. Leaf = matter, ember = heat.
- Glow and particles only on Night.
- New versions get `_v3`, never overwrite approved files. Superseded logos live in `05_logo_primary/superseded/`.
- Every figure shown in an asset carries MODEL, SIMULATED or MEASURED.

## Regenerate
```bash
.venv/bin/python brand/src/extract_mark.py
.venv/bin/python brand/src/mark.py
.venv/bin/python brand/src/assets.py
```

<!-- Asset index generated 2026-10-21 22:53 -->

## Asset Inventory

| Folder | File | Status | Size | Model | Notes |
|---|---|---|---|---|---|
| `00_moodboard` | `logo-reference-v2.png` | Approved | 1630 KB |  |  |
| `00_moodboard` | `logo-reference.png` | Approved | 1599 KB |  |  |
| `00_moodboard` | `mood-2.png` | Approved | 701 KB |  |  |
| `00_moodboard` | `mood-3.png` | Approved | 679 KB |  |  |
| `00_moodboard` | `mood-4.png` | Approved | 397 KB |  |  |
| `00_moodboard` | `mood-5.png` | Approved | 726 KB |  |  |
| `01_intake` | `answers.md` | Reference | 2 KB |  |  |
| `01_intake` | `mode.md` | Reference | 0 KB |  |  |
| `01_intake` | `references.md` | Reference | 2 KB |  |  |
| `02_direction` | `picked.md` | Reference | 0 KB |  |  |
| `02_direction` | `territories.md` | Reference | 1 KB |  |  |
| `03_system` | `colors.md` | Reference | 2 KB |  |  |
| `03_system` | `lift.md` | Reference | 2 KB |  |  |
| `03_system` | `shape.md` | Reference | 1 KB |  |  |
| `03_system` | `typography.md` | Reference | 2 KB |  |  |
| `03_system` | `voice.md` | Reference | 1 KB |  |  |
| `04_manifest` | `manifest.md` | Reference | 2 KB |  |  |
| `04_manifest` | `medium.md` | Reference | 0 KB |  |  |
| `05_logo_primary` | `gate2_sheet_v2.png` | Approved | 800 KB |  |  |
| `05_logo_primary` | `mark_v2_dark.png` | Approved | 959 KB |  |  |
| `05_logo_primary` | `mark_v2_light.png` | Approved | 836 KB |  |  |
| `05_logo_primary` | `primary_v2.png` | Locked | 608 KB | none |  |
| `05_logo_primary` | `primary_v2.svg` | Locked | 1303 KB | none |  |
| `05_logo_primary` | `primary_v2_light.png` | Locked | 623 KB |  |  |
| `05_logo_primary` | `primary_v2_light.svg` | Locked | 1138 KB |  |  |
| `05_logo_primary` | `source_artwork.png` | Approved | 1630 KB |  |  |
| `06_logo_variants` | `app_icon_512.png` | Approved | 205 KB |  |  |
| `06_logo_variants` | `apple-touch-icon.png` | Approved | 30 KB |  |  |
| `06_logo_variants` | `favicon-16.png` | Approved | 1 KB |  |  |
| `06_logo_variants` | `favicon-32.png` | Approved | 2 KB |  |  |
| `06_logo_variants` | `favicon-48.png` | Approved | 3 KB |  |  |
| `06_logo_variants` | `favicon.svg` | Approved | 15 KB |  |  |
| `06_logo_variants` | `horizontal_dark.png` | Approved | 146 KB |  |  |
| `06_logo_variants` | `horizontal_dark.svg` | Approved | 1303 KB |  |  |
| `06_logo_variants` | `horizontal_light.png` | Approved | 148 KB |  |  |
| `06_logo_variants` | `horizontal_light.svg` | Approved | 1139 KB |  |  |
| `06_logo_variants` | `mark_mono_dark.svg` | Approved | 17 KB |  |  |
| `06_logo_variants` | `mark_mono_light.svg` | Approved | 17 KB |  |  |
| `06_logo_variants` | `mark_ring_dark.png` | Approved | 959 KB |  |  |
| `06_logo_variants` | `mark_ring_light.png` | Approved | 836 KB |  |  |
| `06_logo_variants` | `stacked_dark_transparent.svg` | Approved | 1303 KB |  |  |
| `06_logo_variants` | `stacked_light_transparent.svg` | Approved | 1138 KB |  |  |
| `06_logo_variants` | `wordmark_dark.png` | Approved | 26 KB |  |  |
| `06_logo_variants` | `wordmark_dark.svg` | Approved | 23 KB |  |  |
| `06_logo_variants` | `wordmark_light.png` | Approved | 26 KB |  |  |
| `06_logo_variants` | `wordmark_light.svg` | Approved | 23 KB |  |  |
| `09_marketing` | `drawing_titleblock_mark.svg` | Approved | 15 KB |  |  |
| `09_marketing` | `github_social_1280x640.png` | Approved | 375 KB |  |  |
| `09_marketing` | `hero_16x9.png` | Approved | 1011 KB |  |  |
| `09_marketing` | `og_1200x630.png` | Approved | 483 KB |  |  |
| `09_marketing` | `readme_banner_dark.png` | Approved | 333 KB |  |  |
| `09_marketing` | `readme_banner_light.png` | Approved | 332 KB |  |  |
| `09_marketing` | `video_end.png` | Approved | 535 KB |  |  |
| `09_marketing` | `video_title.png` | Approved | 646 KB |  |  |
| `10_color` | `palette_v1.png` | Approved | 57 KB |  |  |
| `10_color` | `tokens.json` | Reference | 1 KB |  |  |
| `11_typography` | `specimen.png` | Approved | 904 KB |  |  |
| `11_typography` | `typography_spec.md` | Reference | 1 KB |  |  |
| `12_docs` | `AGENTS.md` | Reference | 2 KB |  |  |
| `12_docs` | `Brand-Booklet.md` | Reference | 14 KB |  |  |
| `12_docs` | `Brand.md` | Reference | 1 KB |  |  |
| `12_docs` | `design-system.md` | Reference | 6 KB |  |  |


## Locked Files (Do Not Modify Without User Approval)

- `./brand/05_logo_primary/primary_v2.png`
- `./brand/05_logo_primary/primary_v2.svg`
- `./brand/05_logo_primary/primary_v2_light.png`
- `./brand/05_logo_primary/primary_v2_light.svg`

