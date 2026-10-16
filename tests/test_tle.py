from conjunction_screener import load_sample_tles, parse_tle_text


def test_parse_sample_file():
    records = load_sample_tles()
    assert len(records) >= 10
    for rec in records:
        assert rec.name
        assert rec.line1.startswith("1 ")
        assert rec.line2.startswith("2 ")


def test_parse_handles_missing_name_line():
    text = (
        "1 25544U 98067A      26288.82192346  .00005580  00000+0  10980-3 0  9999\n"
        "2 25544  51.6317  63.1136 0006755 265.8514  94.1703 15.48879905590452\n"
    )
    records = parse_tle_text(text)
    assert len(records) == 1
    assert "25544" in records[0].name


def test_first_record_is_iss():
    records = load_sample_tles()
    assert "25544" in records[0].line1


def test_dedupe_same_orbit_merges_docked_modules():
    from conjunction_screener import dedupe_same_orbit
    records = load_sample_tles()
    unique = dedupe_same_orbit(records)
    assert len(unique) < len(records)
    names = [r.name for r in unique]
    assert "ISS (ZARYA)" in names
    assert "POISK" not in names  # same orbit as ZARYA, merged away
