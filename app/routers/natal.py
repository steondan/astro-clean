# app/routers/natal.py
from __future__ import annotations
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from zoneinfo import ZoneInfo
import swisseph as swe

from app.services.astro import calc_chart
from app.services.astro.parts import calc_part_of_fortune
from app.services.astro.san import calc_prenatal_lunations
from app.services.astro.eclipses import calc_next_eclipses

router = APIRouter(prefix="/natal", tags=["natal"])


def _to_jd_utc(date: str, time: str, tz: str) -> float:
    """JD(UT) из локальных date/time и IANA tz."""
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


def _parse_stars_param(stars: Optional[str]) -> Optional[List[str]]:
    if not stars:
        return None
    items = [s.strip() for s in stars.split(",")]
    return [s for s in items if s]


@router.get("/chart")
def natal_chart(
    # обязательные
    date: str = Query(..., example="1971-06-22"),
    time: str = Query(..., example="02:30:00"),
    lat: float = Query(..., example=59.4167),
    lon: float = Query(..., example=24.75),
    tz: str = Query("UTC", example="Europe/Tallinn"),

    # настройки
    houseSystem: str = Query(
        "Placidus",
        description="Placidus | Koch | Equal | WholeSign | Alcabitius | Porphyry"
    ),
    nodes: str = Query("true", description="true | mean"),
    stars: Optional[str] = Query(None, example="Sirius,Regulus,Spica"),
    detail: bool = Query(True),

    # Pars Fortunae
    fortuneUseSect: bool = Query(True, description="Учитывать секту (day/night)"),
    fortuneForceDiurnal: Optional[bool] = Query(None, description="Принудительно день (true) / ночь (false)"),

    # Затмения
    eclipses: bool = Query(False, description="Включить ближайшие затмения (глобально)"),
):
    # Основной расчёт (планеты, дома, углы)
    try:
        star_list = _parse_stars_param(stars)
        bodies, houses, angles, ephemeris, extra = calc_chart(
            date, time, lat, lon, tz, houseSystem, nodes, star_list, detail
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=f"Calc error: {e}")

    # JD(UT) нужен для PoF и затмений
    jd_ut = _to_jd_utc(date, time, tz)

    # Pars Fortunae
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

    # SAN1 / SAN2 — преднатальные новолуние и полнолуние
    try:
        san = calc_prenatal_lunations(date, time, lat, lon, tz)
    except Exception as e:
        raise HTTPException(400, detail=f"SAN error: {e}")

    # Затмения (опционально)
    eclipses_out: Optional[Dict[str, Any]] = None
    if eclipses:
        try:
            eclipses_out = calc_next_eclipses(jd_ut)
        except Exception as e:
            raise HTTPException(400, detail=f"Eclipses error: {e}")

    # Итоговый ответ
    resp: Dict[str, Any] = {
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
    if eclipses_out is not None:
        resp["extras"]["Eclipses"] = eclipses_out

    return resp