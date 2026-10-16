"""conjunction_screener: educational satellite close-approach screening."""

from .tle import (TleRecord, parse_tle_text, load_tle_file, load_sample_tles, fetch_group, dedupe_same_orbit)
from .propagate import satrec_from_tle, position_eci_km, propagate, EARTH_RADIUS_KM
from .screen import CloseApproach, screen_pair, screen_catalog, closest_approach

__version__ = "0.1.0"
