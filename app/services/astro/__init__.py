from .planets import calc_planets
from .moon import calc_moon
from .nodes import calc_nodes
from .houses import calc_houses
import swisseph as swe

def _to_jd_ut(dt_utc):
    h = dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0 + dt_utc.microsecond/3_600_000_000.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, h)

def calc_chart(dt_utc, lat, lon, nodes_kind, houseSystem, detail, stars=None, eclipses=False):
    jd_ut = _to_jd_ut(dt_utc)
    bodies = {}
    bodies.update(calc_planets(jd_ut, detail=detail))  # Sun..Saturn
    bodies["Moon"] = calc_moon(jd_ut, detail=detail)
    bodies["LunarNode"] = calc_nodes(jd_ut, nodes_kind or "mean")
    houses, angles = calc_houses(jd_ut, lat, lon, houseSystem)
    return bodies, houses, angles, "Swiss Ephemeris", {}
