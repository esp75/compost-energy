# Asset manifest

All assets are vector or rendered from code by `brand/src/` (no image model). PNG exports via `brand/src/render.mjs` (headless Chrome).

| File | Size / AR | Notes |
|---|---|---|
| 05_logo_primary/primary_v1.svg/.png | 1200×1200 | Stacked, Night, glow + particles (hero use) |
| 05_logo_primary/primary_v1_light.svg/.png | 1200×1200 | Stacked, Mist, no glow |
| 06_logo_variants/horizontal_{dark,light}.svg/.png | 1600×400 | Mark left, wordmark right |
| 06_logo_variants/stacked_{dark,light}_transparent.svg | 1200×1200 | No background |
| 06_logo_variants/mark_{lines,flat,mono-light,mono-dark}.svg | 512×512 | Mark only |
| 06_logo_variants/wordmark_{dark,light}.svg | 1600×260 | COMPOST + ENERGY only |
| 06_logo_variants/favicon.svg, favicon-{16,32,48}.png, apple-touch-icon.png (180), app_icon_512.png | square | Flat mark, Night tile for app icon |
| 09_marketing/github_social_1280x640.png | 1280×640 | Repo social preview |
| 09_marketing/readme_banner_{light,dark}.svg/.png | 1600×480 | README header via `<picture>` |
| 09_marketing/og_1200x630.png | 1200×630 | Website OG card |
| 09_marketing/hero_16x9.png | 1920×1080 | Procedural hero (particle ring + contour field) |
| 09_marketing/video_title.png, video_end.png | 1920×1080 | Demo video cards |
| 09_marketing/drawing_titleblock_mark.svg | small | Mark for drawing title blocks |
| 10_color/palette_v1.png | 1600×900 | Palette visualisation |
| 11_typography/typography_spec.md (+ specimen.png) | — | Type spec |

Excluded: patches, stickers (no use in this project).
