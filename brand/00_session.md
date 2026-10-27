# Compost Energy brand: session log

Project: Compost Energy (open-hardware compost heat recovery, farm scale)
Started: 2026-10-21 20:57
Skill: brand-booklet, mode INSPIRED with a locked logo (see 01_intake/mode.md)
Deviations agreed with Maxime: no fal / gpt-image-2 (procedural imagery only); logo rebuilt as vector;
high-end-visual-design and claude-taste are not installed, replaced by frontend-design guidance + a fresh-eyes design review.

## Phase 0 — Preflight & Mode Router · 2026-10-21 20:57
Status: complete
Key decisions:
- Mode INSPIRED, logo locked (new logo supplied, four mood-board references)
- Fonts fetched under OFL into 11_typography/fonts/
Files written/updated:
- 01_intake/mode.md, 00_moodboard/*
Next phase: Intake
Resume hint: read 01_intake/answers.md

## Phase 1 — Intake · 2026-10-21 20:57
Status: complete
Key decisions:
- Answers pre-filled from the repo and earlier sessions (no FrenchPOC/FPC mentions)
- Reference synthesis written for the logo + 4 mood images
Files written/updated:
- 01_intake/answers.md, 01_intake/references.md, 00_plan.md
Next phase: Direction
Resume hint: direction already picked by Maxime (Hybrid)

## Phase 2 — Direction · 2026-10-21 20:57
Status: complete
Key decisions:
- Hybrid territory picked by Maxime on 2026-10-21
Files written/updated:
- 02_direction/territories.md, 02_direction/picked.md, 00_plan.md
Next phase: Visual system (gate 1)
Resume hint: present 03_system for approval

## Phase 3 — Visual system · 2026-10-21 20:59
Status: partial (awaiting gate 1)
Key decisions:
- Two grounds (Night #060a07 / Mist #e3eae5), leaf = matter, ember = heat, all text pairs AA
- Unbounded (wordmark, figures) + Instrument Sans (text) + Geist Mono (data); Michroma shown as alternative
- Hairline rhythm, 28 px glass cards with notch, ring + crosshair, contour texture; voice precise · calm · candid
Files written/updated:
- 03_system/{lift,colors,typography,shape,voice}.md, 10_color/tokens.json, 03_system/specimen_v1.png, src/specimen.html, src/render.mjs
Next phase: Medium + manifest, then primary logo (gate 2)
Resume hint: wait for Maxime's gate-1 answer

## Phase 3 — Visual system (gate 1) · 2026-10-21 21:09
Status: complete
Key decisions:
- Maxime approved the system; wordmark must be recreated after the reference logo's own lettering (not Unbounded/Michroma)
- COMPOST rebuilt as custom heavy extended rounded-square letters; ENERGY in Michroma (thin, tracked) as in the reference
Next phase: Manifest

## Phase 4 — Medium + manifest · 2026-10-21 21:09
Status: complete
Files written/updated: 04_manifest/medium.md, 04_manifest/manifest.md

## Phase 5 — Primary logo · 2026-10-21 21:09
Status: awaiting gate 2
Files written/updated: 05_logo_primary/primary_v1{,_light}.svg/.png, gate2_sheet.png, src/mark.py
Resume hint: on approval, run Phase 6 asset generation from src/

## Phase 5 — Primary logo v2 · 2026-10-21 22:19
Status: awaiting gate 2 (v2)
Key decisions:
- Maxime supplied a final logo (00_moodboard/logo-reference-v2.png): "use this one"
- Ring = Maxime's artwork, lifted off black by src/extract_mark.py (dark: exact alpha; light: alpha x2.5)
- Hand-drawn vector ring attempts (v1 two crescents, v2 three ribbons) dropped as the master; vector kept only for <= 32 px and one-colour
- COMPOST re-drawn as vector to match the supplied lettering (pill-shaped, wide, medium-heavy); ENERGY = Lexend Zetta Light, tracked 1.55 em; tapered gradient rules
Files written/updated: 05_logo_primary/primary_v2{,_light}.svg/.png, mark_v2_{dark,light}.png, gate2_sheet_v2.png, src/extract_mark.py, src/mark.py

## Phase 5 — gate 2 · 2026-10-21 22:51
Status: complete — Maxime approved v2

## Phase 6 — Assets · 2026-10-21 22:51
Status: complete
Files: 06_logo_variants/*, 09_marketing/*, 10_color/palette_v1.png, 11_typography/specimen.png (all by src/assets.py)

## Phase 7 — Audit · 2026-10-21 22:51
Status: complete — 00_review.md, all >= 5/8, none regenerated
Next phase: Docs

## Phase 8 — Docs · 2026-10-21 22:53
Status: complete — 12_docs/{Brand-Booklet.md (259 lines), Brand.md, design-system.md, AGENTS.md}
Next phase: HTML booklet + PDF

## Phase 9 — HTML booklet · 2026-10-21 22:55
Status: complete — 13_booklet/booklet.html (+ booklet.local.html wrapper for local render), assets/, design-notes.md
Published: https://claude.ai/artifact/3K8GVxpqJxRRG7ae8HVQx8

## Phase 10 — PDF · 2026-10-21 22:55
Status: complete — 13_booklet/booklet.pdf (4.6 MB, A4 landscape), build.log
Workflow complete.
