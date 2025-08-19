import swisseph as swe

def _norm360(x: float) -> float:
    x = x % 360.0
    return x + 360.0 if x < 0 else x

def calc_nodes(jd_ut: float, kind: str = "mean"):
    """Возвращает лунный узел (северный). kind: 'mean' или 'true'."""
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    if str(kind).lower() in ("true", "true node"):
        pid = swe.TRUE_NODE
    else:
        pid = swe.MEAN_NODE
    xx, _rf = swe.calc_ut(jd_ut, pid, flags)
    lon, lat, dist, slon, slat, sdist = xx
    return {
        "lon": _norm360(lon),
        "lat": lat,
        "dist": dist,
        "spd_lon": slon,
        "spd_lat": slat,
        "spd_dist": sdist,
    }
