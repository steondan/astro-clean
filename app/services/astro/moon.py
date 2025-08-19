import swisseph as swe

def _norm360(x: float) -> float:
    x = x % 360.0
    return x + 360.0 if x < 0 else x

def calc_moon(jd_ut: float, detail: bool = True):
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    xx, _rf = swe.calc_ut(jd_ut, swe.MOON, flags)
    lon, lat, dist, slon, slat, sdist = xx
    out = {"lon": _norm360(lon)}
    if detail:
        out.update({
            "lat": lat, "dist": dist,
            "spd_lon": slon, "spd_lat": slat, "spd_dist": sdist
        })
    return out
