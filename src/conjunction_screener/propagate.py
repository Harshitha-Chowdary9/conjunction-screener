"""SGP4 orbit propagation to Earth-centred inertial (ECI) positions.

SGP4 is the standard propagator designed for TLE data. Positions are
returned in the TEME frame in kilometres.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
from sgp4.api import Satrec, jday

from .tle import TleRecord

EARTH_RADIUS_KM = 6378.135  # WGS-72 equatorial radius, the model SGP4 uses


def satrec_from_tle(record: TleRecord) -> Satrec:
    sat = Satrec.twoline2rv(record.line1, record.line2)
    if sat.error != 0:
        raise ValueError(f"could not parse TLE for {record.name!r} (error {sat.error})")
    return sat


def position_eci_km(sat: Satrec, when: datetime) -> np.ndarray:
    """ECI (TEME) position of one satellite at one UTC instant, in km."""
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    jd, fr = jday(
        when.year, when.month, when.day,
        when.hour, when.minute, when.second + when.microsecond * 1e-6,
    )
    error, r, _v = sat.sgp4(jd, fr)
    if error != 0:
        raise ValueError(f"SGP4 propagation failed (error {error})")
    return np.array(r, dtype=float)


def propagate(sat: Satrec, start: datetime, step_seconds: float, count: int):
    """Propagate a satellite over a regular time grid.

    Returns (times, positions) where positions has shape (count, 3).
    """
    times = [start + timedelta(seconds=step_seconds * i) for i in range(count)]
    positions = np.array([position_eci_km(sat, t) for t in times])
    return times, positions
