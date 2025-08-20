# app/services/astro/daynight.py
from __future__ import annotations
import math
import swisseph as swe

def _norm360(x: float) -> float:
    x %= 360.0
    return x + 360.0 if x < 0 else x

def is_diurnal(jd_ut: float, lat_deg: float, lon_deg: float) -> bool:
    """
    True, если Солнце выше геометрического горизонта (истинный день),
    иначе False (ночь). Считаем по экваториальным координатам и LST.
    """
    # Экваториальные координаты Солнца: RA (°), Dec (°)
    x_equ, _ = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
    ra_deg, dec_deg = float(x_equ[0]), float(x_equ[1])

    ra = math.radians(ra_deg)
    dec = math.radians(dec_deg)

    # Местное звёздное время (часы) -> часовой угол H (рад)
    gst_h = swe.sidtime(jd_ut)
    lst_h = gst_h + lon_deg / 15.0
    H = math.radians((lst_h % 24.0) * 15.0) - ra

    phi = math.radians(lat_deg)
    sin_h = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(H)
    return sin_h > 0.0