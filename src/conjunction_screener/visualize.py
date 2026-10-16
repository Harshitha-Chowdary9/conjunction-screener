"""Simple 3D visualisation of a close approach between two objects."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless rendering

import matplotlib.pyplot as plt
import numpy as np

from .propagate import EARTH_RADIUS_KM, position_eci_km, propagate, satrec_from_tle
from .screen import CloseApproach
from .tle import TleRecord


def _earth_wireframe(ax, radius: float = EARTH_RADIUS_KM) -> None:
    u = np.linspace(0, 2 * np.pi, 40)
    v = np.linspace(0, np.pi, 20)
    x = radius * np.outer(np.cos(u), np.sin(v))
    y = radius * np.outer(np.sin(u), np.sin(v))
    z = radius * np.outer(np.ones_like(u), np.cos(v))
    ax.plot_wireframe(x, y, z, color="steelblue", alpha=0.25, linewidth=0.5)


def plot_close_approach(
    rec_a: TleRecord,
    rec_b: TleRecord,
    approach: CloseApproach,
    output_path,
    half_window_minutes: float = 95.0,
    samples: int = 300,
):
    """Plot both orbits around the approach time and mark the closest point.

    The window defaults to roughly one low-Earth orbital period on each
    side of the approach.
    """
    sat_a, sat_b = satrec_from_tle(rec_a), satrec_from_tle(rec_b)
    start = approach.time - timedelta(minutes=half_window_minutes)
    step = 2.0 * half_window_minutes * 60.0 / samples
    _, pos_a = propagate(sat_a, start, step, samples)
    _, pos_b = propagate(sat_b, start, step, samples)

    pa = position_eci_km(sat_a, approach.time)
    pb = position_eci_km(sat_b, approach.time)

    fig = plt.figure(figsize=(9, 8))
    ax = fig.add_subplot(111, projection="3d")
    _earth_wireframe(ax)
    ax.plot(pos_a[:, 0], pos_a[:, 1], pos_a[:, 2], color="darkorange", lw=1.2, label=rec_a.name)
    ax.plot(pos_b[:, 0], pos_b[:, 1], pos_b[:, 2], color="seagreen", lw=1.2, label=rec_b.name)
    ax.scatter(*pa, color="darkorange", s=40)
    ax.scatter(*pb, color="seagreen", s=40)
    ax.plot(
        [pa[0], pb[0]], [pa[1], pb[1]], [pa[2], pb[2]],
        color="red", lw=2.0, label=f"closest approach: {approach.distance_km:.1f} km",
    )

    limit = max(
        np.abs(pos_a).max(), np.abs(pos_b).max(), EARTH_RADIUS_KM
    ) * 1.05
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)
    ax.set_xlabel("x (km, TEME)")
    ax.set_ylabel("y (km, TEME)")
    ax.set_zlabel("z (km, TEME)")
    ax.set_title(
        f"{rec_a.name} x {rec_b.name}\n"
        f"{approach.time:%Y-%m-%d %H:%M:%S} UTC, miss distance {approach.distance_km:.2f} km"
    )
    ax.legend(loc="upper left", fontsize=8)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path
