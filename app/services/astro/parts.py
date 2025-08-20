# app/services/astro/parts.py
from __future__ import annotations
from typing import Optional, Dict, Any
import swisseph as swe
from .daynight import is_diurnal

def _norm360(x: float) -> float:
    x %= 360.0
    return x + 360.0 if x < 0 else x

def calc_part_of_fortune(
    jd_ut: float,
    asc_lon_deg: float,
    sun_lon_deg: float,
    moon_lon_deg: float,
    lat_deg: float,
    lon_deg: float,
    *,
    use_sect: bool = True,
    force_diurnal: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Pars Fortunae (зодиакальная долгота):
      - дневная:  ASC + Moon − Sun
      - ночная:  ASC + Sun  − Moon
    use_sect=True — учитывать секту, иначе всегда дневная формула.
    force_diurnal=None — авто (по высоте Солнца). True/False — форс.
    """
    if use_sect:
        diurnal = is_diurnal(jd_ut, lat_deg, lon_deg) if force_diurnal is None else bool(force_diurnal)
        if diurnal:
            lon = asc_lon_deg + moon_lon_deg - sun_lon_deg
        else:
            lon = asc_lon_deg + sun_lon_deg - moon_lon_deg
    else:
        diurnal = None
        lon = asc_lon_deg + moon_lon_deg - sun_lon_deg

    return {
        "lon": _norm360(lon),
        "diurnal": diurnal,
        "formula": "ASC+Moon−Sun (day) / ASC+Sun−Moon (night)" if use_sect else "ASC+Moon−Sun (always)",
        "engine": "derived"
    }