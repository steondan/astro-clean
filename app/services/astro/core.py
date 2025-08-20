# app/services/astro/core.py
from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime
from zoneinfo import ZoneInfo
import swisseph as swe

from .planets import calc_planets
from .moon import calc_moon
from .nodes import calc_nodes
from .houses import calc_houses
from .stars import calc_stars

def _to_jd_utc(date: str, time: str, tz: str) -> float:
    try:
        dt_local = datetime.fromisoformat(f"{date}T{time}")
    except Exception:
        raise ValueError("Invalid date/time. Expected date=YYYY-MM-DD, time=HH:MM[:SS]")
    try:
        z = ZoneInfo(tz)
    except Exception:
        raise ValueError(f"Unknown timezone: {tz}")
    dt_utc = dt_local.replace(tzinfo=z).astimezone(ZoneInfo("UTC"))
    ut = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut)

def _parse_stars_arg(stars: Optional[Union[str, List[str]]]) -> List[str]:
    if stars is None:
        return []
    if isinstance(stars, list):
        return [s.strip() for s in stars if isinstance(s, str) and s.strip()]
    if isinstance(stars, str):
        return [s.strip() for s in stars.split(",") if s.strip()]
    raise ValueError("stars must be a comma-separated string or list of names")

def calc_chart(
    date: str,
    time: str,
    lat: float,
    lon: float,
    tz: str,
    houseSystem: str = "Placidus",
    nodes: str = "true",
    stars: Optional[Union[str, List[str]]] = None,
    detail: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, float], str, Dict[str, Any]]:
    jd_ut = _to_jd_utc(date, time, tz)

    bodies: Dict[str, Any] = {}
    bodies.update(calc_planets(jd_ut, detail=detail))
    bodies["Moon"] = calc_moon(jd_ut, detail=detail)
    bodies["LunarNode"] = calc_nodes(jd_ut, nodes or "true")

    houses, angles = calc_houses(jd_ut, lat, lon, houseSystem)

    extras: Dict[str, Any] = {}
    star_list = _parse_stars_arg(stars)
    if star_list:
        try:
            extras["stars"] = calc_stars(jd_ut, star_list)
        except Exception as e:
            extras["stars"] = {"error": f"stars calc failed: {e}"}

    return bodies, houses, angles, "Swiss Ephemeris", extras