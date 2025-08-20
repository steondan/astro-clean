# app/routers/natal.py
from __future__ import annotations
from typing import Optional, List, Any
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from zoneinfo import ZoneInfo
import swisseph as swe

from app.services.astro import calc_chart
from app.services.astro.parts import calc_part_of_fortune
from app.services.astro.san import calc_prenatal_lunations

router = APIRouter(prefix="/natal", tags=["natal"])


def _to_jd_utc(date: str, time: str, tz: str) -> float:
    try:
        dt_local = datetime.fromisoformat(f"{date}T{time}")
    except Exception:
        raise HTTPException(400, detail="Некорректные дата/время. Ожидаю date=YYYY-MM-DD, time=HH:MM[:SS]")
    try:
        z = ZoneInfo(tz)
    except Exception:
        raise HTTPException(400, detail=f"Неизвестная таймзона: {tz}")
    dt_utc = dt_local.replace(tzinfo=z).astimezone(ZoneInfo("UTC"))
    ut = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut)


def _normalize_stars(stars_param: Any) -> Optional[List[str]]:
    if stars_param is None:
        return None
    items: List[str] = []
    if isinstance(stars_param, (list, tuple)):
        for it in stars_param:
            if not it:
                continue
            if isinstance(it, str):
                items.extend(s.strip() for s in it.split(",") if s.strip())
    elif isinstance(stars_param, str):
        items = [s.strip() for s in stars_param.split(",") if s.strip()]
    else:
        return None
    return items or None


@router.get("/chart")
def natal_chart(
    date: str = Query(..., example="1971-06-22"),
    time: str = Query(..., example="02:30:00"),
    lat: float = Query(..., example=59.4167),
    lon: float = Query(..., example=24.75),
    tz: str = Query("UTC", example="Europe/Tallinn"),
    houseSystem: str = Query("Placidus", description="Placidus | Koch | Equal | WholeSign | Alcabitius | Porphyry"),
    nodes: str = Query("true", description="true | mean"),
    stars: Optional[List[str]] = Query(None, description="Повторяющийся параметр или comma-separated"),
    detail: bool = Query(True),
    fortuneUseSect: bool = Query(True),
    fortuneForceDiurnal: Optional[bool] = Query(None),
):
    try:
        star_list = _normalize_stars(stars)
        bodies, houses, angles, ephemeris, extra = calc_chart(
            date, time, lat, lon, tz, houseSystem, nodes, star_list, detail
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=f"Calc error: {e}")

    jd_ut = _to_jd_utc(date, time, tz)

    try:
        pof = calc_part_of_fortune(
            jd_ut=jd_ut,
            asc_lon_deg=angles["ASC"],
            sun_lon_deg=bodies["Sun"]["lon"],
            moon_lon_deg=bodies["Moon"]["lon"],
            lat_deg=lat,
            lon_deg=lon,
            use_sect=fortuneUseSect,
            force_diurnal=fortuneForceDiurnal,
        )
    except Exception as e:
        raise HTTPException(400, detail=f"PoF error: {e}")

    try:
        san = calc_prenatal_lunations(date, time, lat, lon, tz)
    except Exception as e:
        raise HTTPException(400, detail=f"SAN error: {e}")

    return {
        "bodies": bodies,
        "houses": houses,
        "angles": angles,
        "ephemeris": ephemeris,
        "extras": {
            **extra,
            "PartOfFortune": pof,
            **san
        }
    }