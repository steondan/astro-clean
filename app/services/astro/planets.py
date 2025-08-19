import swisseph as swe

# Sun..Saturn (без Луны)
PLANETS = [
    ("Sun", swe.SUN),
    ("Mercury", swe.MERCURY),
    ("Venus", swe.VENUS),
    ("Mars", swe.MARS),
    ("Jupiter", swe.JUPITER),
    ("Saturn", swe.SATURN),
]

def _norm360(x: float) -> float:
    x = x % 360.0
    return x + 360.0 if x < 0 else x

def _to_dict(xx, detail: bool):
    lon, lat, dist, slon, slat, sdist = xx
    out = {"lon": _norm360(lon)}
    if detail:
        out.update({
            "lat": lat, "dist": dist,
            "spd_lon": slon, "spd_lat": slat, "spd_dist": sdist
        })
    return out

def calc_planets(jd_ut: float, detail: bool = True):
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    bodies = {}
    for name, pid in PLANETS:
        xx, _rf = swe.calc_ut(jd_ut, pid, flags)
        bodies[name] = _to_dict(xx, detail)
    return bodies
