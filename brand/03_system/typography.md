# Typography

All three families are SIL Open Font License, files in `11_typography/fonts/`.

| Role | Family | Why |
|---|---|---|
| Wordmark + display | **Unbounded** (600–800, caps for the wordmark) | Extended, geometric, rounded terminals: matches the wide heavy letters in the logo reference without the sci-fi feel of Michroma/Orbitron. Variable weight, so the wordmark and big numbers share one face. |
| Headlines + body | **Instrument Sans** (400/500/600, width 100) | A quiet neo-grotesk close to mood 2 and 5 type; holds up at 72 px and at 14 px. |
| Data, drawings, code | **Geist Mono** (400/500) | Tabular figures for temperatures, kW and tags (T-101, CE-12). |

Alternative shown at the gate: **Michroma** for the wordmark only (wider, single weight, more technical).

## Scale (screen)

| Step | Size | Family / weight | Tracking |
|---|---|---|---|
| display | `clamp(3rem, 8vw, 7.5rem)` | Instrument Sans 500 | -0.035em |
| h1 | `clamp(2.25rem, 5vw, 4rem)` | Instrument Sans 500 | -0.03em |
| h2 | `clamp(1.6rem, 3vw, 2.5rem)` | Instrument Sans 500 | -0.02em |
| h3 | `1.25rem` | Instrument Sans 600 | -0.01em |
| figure | `clamp(2rem, 4vw, 3.5rem)` | Unbounded 600 | -0.02em |
| body | `1.0625rem / 1.6` | Instrument Sans 400 | 0 |
| small | `0.875rem / 1.5` | Instrument Sans 400 | 0 |
| label | `0.75rem` | Geist Mono 500, caps | 0.12em |
| button | `0.9375rem` | Instrument Sans 500 | 0 |

Wordmark: COMPOST is custom vector lettering (pill-shaped, extended) drawn after the logo; ENERGY is Lexend Zetta Light, caps, tracked 1.55 em, between a leaf rule and an ember rule. Unbounded is kept for big figures only.

Print: body 10/14 pt Instrument Sans, labels 7 pt Geist Mono.
