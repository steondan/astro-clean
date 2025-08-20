from __future__ import annotations
from typing import Optional, Dict, Any, List
import swisseph as swe
from datetime import datetime
from zoneinfo import ZoneInfo

from .planets import calc_planets
from .moon import calc_moon
from .nodes import calc_nodes
from .houses import calc_houses
from .stars import calc_stars


def _to_jd_utc(date: str, time: str, tz: str) -> float:
    dt_local = datetime.fromisoformat(f"{date}T{time}")
    z = ZoneInfo(tz)
    dt_utc = dt_local.replace(tzinfo=z).astimezone(ZoneInfo("UTC"))
    ut = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut)


def calc_chart(
    date: str,
    time: str,
    lat: float,
    lon: float,
    tz: str,
    houseSystem: str,
    nodes_kind: str,
    stars: Optional[str],
    detail: bool,
):
    jd_ut = _to_jd_utc(date, time, tz)

    bodies: Dict[str, Any] = {}
    bodies.update(calc_planets(jd_ut, detail=detail))
    bodies["Moon"] = calc_moon(jd_ut, detail=detail)
    bodies["LunarNode"] = calc_nodes(jd_ut, nodes_kind or "mean")

    houses, angles = calc_houses(jd_ut, lat, lon, houseSystem)

    extra: Dict[str, Any] = {}
    if stars:
        star_list: List[str] = [s.strip() for s in stars.split(",") if s.strip()]
        if star_list:
            extra["stars"] = calc_stars(jd_ut, star_list)

    return bodies, houses, angles, "Swiss Ephemeris", extra