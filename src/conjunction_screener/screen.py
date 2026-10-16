"""Pairwise close-approach (conjunction) screening.

The method is deliberately simple and educational:

1. Propagate both objects on a coarse time grid with SGP4.
2. Flag grid points where the separation is a local minimum below a
   distance threshold.
3. Refine each candidate with a golden-section search between the
   neighbouring grid points.

Real operational screening adds covariance, probability of collision and
much larger catalogs; this project keeps only the geometry.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np

from .propagate import (
    EARTH_RADIUS_KM,
    position_eci_km,
    propagate,
    satrec_from_tle,
)
from .tle import TleRecord


@dataclass(frozen=True)
class CloseApproach:
    name_a: str
    name_b: str
    time: datetime            # UTC instant of closest approach
    distance_km: float        # separation at that instant
    altitude_km: float        # mean altitude of the two objects above Earth

    def __str__(self) -> str:
        return (
            f"{self.time:%Y-%m-%d %H:%M:%S} UTC  "
            f"{self.distance_km:8.2f} km  (alt ~{self.altitude_km:6.1f} km)  "
            f"{self.name_a}  x  {self.name_b}"
        )


def _distance_between(sat_a, sat_b, when: datetime) -> float:
    return float(np.linalg.norm(position_eci_km(sat_a, when) - position_eci_km(sat_b, when)))


def _golden_section_min(func, t_lo: datetime, t_hi: datetime, tol_seconds: float = 0.5):
    """Minimise func(t) on [t_lo, t_hi]; returns (t_best, value)."""
    inv_phi = (np.sqrt(5.0) - 1.0) / 2.0
    lo, hi = 0.0, (t_hi - t_lo).total_seconds()

    def at(sec: float) -> float:
        return func(t_lo + timedelta(seconds=sec))

    c = hi - inv_phi * (hi - lo)
    d = lo + inv_phi * (hi - lo)
    while hi - lo > tol_seconds:
        if at(c) < at(d):
            hi = d
        else:
            lo = c
        c = hi - inv_phi * (hi - lo)
        d = lo + inv_phi * (hi - lo)
    t_best = t_lo + timedelta(seconds=(lo + hi) / 2.0)
    return t_best, func(t_best)


def _make_approach(rec_a, rec_b, sat_a, sat_b, t_best, distance) -> CloseApproach:
    r_a = np.linalg.norm(position_eci_km(sat_a, t_best))
    r_b = np.linalg.norm(position_eci_km(sat_b, t_best))
    altitude = (r_a + r_b) / 2.0 - EARTH_RADIUS_KM
    return CloseApproach(rec_a.name, rec_b.name, t_best, float(distance), float(altitude))


def screen_pair(
    rec_a: TleRecord,
    rec_b: TleRecord,
    start: datetime,
    duration_hours: float = 24.0,
    step_seconds: float = 60.0,
    threshold_km: float = 100.0,
) -> list[CloseApproach]:
    """All close approaches between two objects within the window."""
    sat_a, sat_b = satrec_from_tle(rec_a), satrec_from_tle(rec_b)
    count = int(duration_hours * 3600.0 / step_seconds) + 1
    times, pos_a = propagate(sat_a, start, step_seconds, count)
    _, pos_b = propagate(sat_b, start, step_seconds, count)
    distances = np.linalg.norm(pos_a - pos_b, axis=1)

    # Flag every local minimum on the coarse grid, refine it, and only
    # then apply the threshold. Thresholding before refinement would miss
    # dips narrower than the grid step, because the grid points can sit
    # far above the true minimum on both sides.
    approaches: list[CloseApproach] = []
    for i in range(1, count - 1):
        if distances[i] <= distances[i - 1] and distances[i] <= distances[i + 1]:
            t_best, d_best = _golden_section_min(
                lambda t: _distance_between(sat_a, sat_b, t),
                times[i - 1],
                times[i + 1],
            )
            if d_best <= threshold_km:
                approaches.append(_make_approach(rec_a, rec_b, sat_a, sat_b, t_best, d_best))
    return approaches


def closest_approach(
    rec_a: TleRecord,
    rec_b: TleRecord,
    start: datetime,
    duration_hours: float = 24.0,
    step_seconds: float = 30.0,
) -> CloseApproach:
    """The single closest approach of a pair in the window, at any distance."""
    sat_a, sat_b = satrec_from_tle(rec_a), satrec_from_tle(rec_b)
    count = int(duration_hours * 3600.0 / step_seconds) + 1
    times, pos_a = propagate(sat_a, start, step_seconds, count)
    _, pos_b = propagate(sat_b, start, step_seconds, count)
    distances = np.linalg.norm(pos_a - pos_b, axis=1)
    i = int(np.argmin(distances))
    lo = times[max(i - 1, 0)]
    hi = times[min(i + 1, count - 1)]
    t_best, d_best = _golden_section_min(lambda t: _distance_between(sat_a, sat_b, t), lo, hi)
    return _make_approach(rec_a, rec_b, sat_a, sat_b, t_best, d_best)


def screen_catalog(
    records: list[TleRecord],
    start: datetime | None = None,
    duration_hours: float = 24.0,
    step_seconds: float = 60.0,
    threshold_km: float = 100.0,
) -> list[CloseApproach]:
    """Screen every pair in a catalog; results sorted by miss distance."""
    if start is None:
        start = datetime.now(timezone.utc).replace(microsecond=0)
    results: list[CloseApproach] = []
    for rec_a, rec_b in itertools.combinations(records, 2):
        results.extend(
            screen_pair(rec_a, rec_b, start, duration_hours, step_seconds, threshold_km)
        )
    return sorted(results, key=lambda a: a.distance_km)
