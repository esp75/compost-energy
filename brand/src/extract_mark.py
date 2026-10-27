"""Lift the ring from the supplied logo (black background) into RGBA PNGs.

    .venv/bin/python brand/src/extract_mark.py

dark:  alpha = brightness, colour un-premultiplied. Exact on black/Night; keeps the glow.
light: alpha = brightness x 2.5, so the ribbons stay opaque on Mist and only the halo fades.
"""

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "00_moodboard" / "logo-reference-v2.png"
CROP = (330, 0, 1210, 730)          # x0, y0, x1, y1: the ring, above the wordmark


def extract(gain: float, floor: float) -> Image.Image:
    im = np.asarray(Image.open(SRC).convert("RGB").crop(CROP)).astype(np.float32) / 255
    m = im.max(axis=2)
    a = np.clip((m - floor) * gain, 0, 1)
    if gain == 1.0:
        a = np.clip((m - floor) / (1 - floor), 0, 1)
        rgb = np.clip(im / np.maximum(a[..., None], 1e-3), 0, 1)
    else:
        rgb = np.clip(im / np.maximum(m[..., None], 1e-3) * np.clip(m[..., None] * 1.15, 0, 1), 0, 1)
    rgb[a < 1e-3] = 0
    return Image.fromarray((np.dstack([rgb, a]) * 255).astype(np.uint8), "RGBA")


if __name__ == "__main__":
    out = ROOT / "05_logo_primary"
    extract(1.0, 0.02).save(out / "mark_v2_dark.png", optimize=True)
    extract(2.5, 0.06).save(out / "mark_v2_light.png", optimize=True)
    print("wrote", out / "mark_v2_dark.png", out / "mark_v2_light.png")
