"""Shared figure style."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

# Brand tokens (brand/10_color/tokens.json, light "Mist" set): leaf = matter, ember = heat.
INK = "#0f1a13"
MUTED = "#4a5c51"
GRID = "#cfd8d2"
PAPER = "#f4f7f5"
HOT = "#b23f0a"
WARM = "#e0882a"
COOL = "#2f6f73"
GREEN = "#3d6e22"
LIME = "#a7b83f"
PHASE_COLORS = {
    "mesophilic": "#a7b83f",
    "thermophilic": "#e0882a",
    "cooling": "#6f9fa0",
    "maturation": "#7a8f6a",
}

# Instrument Sans and Geist Mono ship with the brand folder (OFL); fall back silently.
_FONTS = Path(__file__).resolve().parents[2] / "brand" / "11_typography" / "fonts"
for _f in ("InstrumentSans.ttf", "GeistMono.ttf"):
    if (_FONTS / _f).exists():
        font_manager.fontManager.addfont(str(_FONTS / _f))

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 160,
    "savefig.bbox": "tight",
    "font.size": 10,
    "font.family": ["Instrument Sans", "DejaVu Sans"],
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
    "savefig.facecolor": PAPER,
    "text.color": INK,
    "axes.titlecolor": INK,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.titlesize": 12,
    "axes.titleweight": "semibold",
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "legend.frameon": False,
})


def simulated_stamp(fig) -> None:
    """Watermark so a figure can never be mistaken for measured data."""
    fig.text(0.995, 0.995, "SIMULATED DATA - not a measurement", ha="right", va="top",
             fontsize=8, color=HOT, alpha=0.8)


def shade_phases(ax, df, x) -> None:
    phase = df["phase"]
    change = phase.ne(phase.shift()).cumsum()
    for _, block in phase.groupby(change):
        ax.axvspan(x[block.index[0]], x[block.index[-1]], color=PHASE_COLORS[block.iloc[0]], alpha=0.35, lw=0)
