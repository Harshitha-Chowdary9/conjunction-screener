"""Two-line element set (TLE) parsing and downloading.

TLEs are the standard public format for satellite orbit data. They are
published by the US Space Command and mirrored by CelesTrak
(https://celestrak.org), which is where this project gets its data.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import urllib.request

CELESTRAK_GROUPS = {
    "stations": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
    "starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
    "active": "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
}

DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE_TLE_FILE = DATA_DIR / "sample_tles.txt"

USER_AGENT = "conjunction-screener/0.1 (educational project)"


@dataclass(frozen=True)
class TleRecord:
    """One named object described by its two TLE lines."""

    name: str
    line1: str
    line2: str


def parse_tle_text(text: str) -> list[TleRecord]:
    """Parse raw TLE text (name line + line 1 + line 2 per object)."""
    records: list[TleRecord] = []
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    i = 0
    while i < len(lines):
        if lines[i].startswith("1 ") and i + 1 < len(lines) and lines[i + 1].startswith("2 "):
            records.append(TleRecord("NORAD " + lines[i][2:7].strip(), lines[i], lines[i + 1]))
            i += 2
        elif i + 2 < len(lines) and lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            records.append(TleRecord(lines[i].strip(), lines[i + 1], lines[i + 2]))
            i += 3
        else:
            i += 1
    return records


def load_tle_file(path) -> list[TleRecord]:
    return parse_tle_text(Path(path).read_text())


def load_sample_tles() -> list[TleRecord]:
    """TLEs bundled with the repo so examples and tests work offline.

    Snapshot of the CelesTrak "stations" group taken on 2026-10-15.
    TLEs age quickly; use fetch_group() for current data.
    """
    return load_tle_file(SAMPLE_TLE_FILE)


def fetch_group(group: str = "stations", timeout: float = 30.0) -> list[TleRecord]:
    """Download current TLEs for a CelesTrak group."""
    if group not in CELESTRAK_GROUPS:
        raise ValueError(f"unknown group {group!r}; choose from {sorted(CELESTRAK_GROUPS)}")
    request = urllib.request.Request(CELESTRAK_GROUPS[group], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        text = response.read().decode("utf-8", errors="replace")
    records = parse_tle_text(text)
    if not records:
        raise RuntimeError(f"no TLEs parsed from CelesTrak group {group!r}")
    return records


def dedupe_same_orbit(records: list[TleRecord]) -> list[TleRecord]:
    """Drop records that share (near-)identical orbital elements.

    CelesTrak lists docked modules of one station as separate objects with
    the same orbit (e.g. ISS (ZARYA), POISK and ISS (NAUKA)). Screening
    them against each other produces meaningless 0.00 km "approaches", so
    we keep only the first record of each identical-element group.
    """
    seen: set[str] = set()
    unique: list[TleRecord] = []
    for rec in records:
        key = rec.line2[8:63]  # orbital elements only: no sat number, rev number, checksum
        if key not in seen:
            seen.add(key)
            unique.append(rec)
    return unique
