from datetime import datetime, timezone

import numpy as np

from conjunction_screener import (
    closest_approach,
    load_sample_tles,
    position_eci_km,
    satrec_from_tle,
    screen_catalog,
    screen_pair,
)

START = datetime(2026, 10, 15, 20, 0, 0, tzinfo=timezone.utc)


def test_identical_object_has_zero_miss_distance():
    iss = load_sample_tles()[0]
    approach = closest_approach(iss, iss, START, duration_hours=2)
    assert approach.distance_km < 1e-6


def test_refinement_beats_coarse_grid():
    records = load_sample_tles()
    rec_a, rec_b = records[0], records[4]
    approach = closest_approach(rec_a, rec_b, START, duration_hours=6, step_seconds=30)

    sat_a, sat_b = satrec_from_tle(rec_a), satrec_from_tle(rec_b)
    # The refined distance must not be worse than the 30 s grid around it.
    for dt in (-30, 0, 30):
        from datetime import timedelta
        t = approach.time + timedelta(seconds=dt)
        coarse = np.linalg.norm(position_eci_km(sat_a, t) - position_eci_km(sat_b, t))
        assert approach.distance_km <= coarse + 1e-9


def test_screen_pair_finds_zero_for_same_object():
    iss = load_sample_tles()[0]
    approaches = screen_pair(iss, iss, START, duration_hours=4, threshold_km=1.0)
    assert approaches
    assert all(a.distance_km < 1e-6 for a in approaches)


def test_catalog_results_are_sorted():
    records = load_sample_tles()[:4]
    approaches = screen_catalog(records, START, duration_hours=4, threshold_km=1e9)
    distances = [a.distance_km for a in approaches]
    assert distances == sorted(distances)
    assert all(a.altitude_km > 100 for a in approaches)
