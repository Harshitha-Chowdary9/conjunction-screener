from datetime import datetime, timezone

import numpy as np

from conjunction_screener import load_sample_tles, position_eci_km, satrec_from_tle
from conjunction_screener.propagate import EARTH_RADIUS_KM, propagate


def _iss():
    return satrec_from_tle(load_sample_tles()[0])


def test_iss_stays_in_low_earth_orbit():
    sat = _iss()
    start = datetime(2026, 10, 15, 20, 0, 0, tzinfo=timezone.utc)
    _, positions = propagate(sat, start, step_seconds=60, count=95)  # ~1 orbit
    radii = np.linalg.norm(positions, axis=1)
    assert radii.min() > EARTH_RADIUS_KM + 200  # above the atmosphere
    assert radii.max() < EARTH_RADIUS_KM + 1000  # not escaping LEO


def test_position_is_finite():
    sat = _iss()
    pos = position_eci_km(sat, datetime(2026, 10, 16, 0, 0, 0, tzinfo=timezone.utc))
    assert pos.shape == (3,)
    assert np.all(np.isfinite(pos))
