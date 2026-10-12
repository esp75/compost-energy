"""Shared figure style."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

INK = "#1f2328"
MUTED = "#6e7781"
GRID = "#d8dee4"
HOT = "#c2410c"
WARM = "#ea8a2e"
COOL = "#2563eb"
GREEN = "#15803d"
PHASE_COLORS = {
    "mesophilic": "#fde68a",
    "thermophilic": "#fca5a5",
    "cooling": "#bfdbfe",
    "maturation": "#d9f99d",
}

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 160,
    "savefig.bbox": "tight",
    "font.size": 10,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
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
