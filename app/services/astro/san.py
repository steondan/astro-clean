# app/services/astro/san.py
from __future__ import annotations
from typing import Literal, Tuple, Dict, Any
import math
import swisseph as swe
from datetime import datetime
from zoneinfo import ZoneInfo

def _norm360(x: float) -> float:
    x %= 360.0
    return x + 360.0 if x < 0 else x

def _angdiff(a: float, b: float) -> float:
    # разность a-b в диапазоне (-180,180]
    d = (a - b + 180.0) % 360.0 - 180.0
    return d

def _moon_sun_longitudes(jd_ut: float) -> Tuple[float, float]:
    mx, _ = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH)
    sx, _ = swe.calc_ut(jd_ut, swe.SUN,  swe.FLG_SWIEPH)
    return _norm360(mx[0]), _norm360(sx[0])

def _f_phase(jd_ut: float, target_deg: float) -> float:
    """
    Нулевая функция для корнепоиска: sin(Δλ − target),
    где Δλ = λ_Luna − λ_Sol. Нуль при новолунии (target=0) и полнолунии (target=180).
    """
    mlon, slon = _moon_sun_longitudes(jd_ut)
    d = _angdiff(mlon, slon) - target_deg
    return math.sin(math.radians(d))

def _bisect_root(jd_left: float, jd_right: float, target_deg: float, max_iter: int = 50, tol_sec: float = 0.25) -> float:
    """
    Бисекция корня f(jd)=sin(Δλ−target)=0 на [left,right]. Требует f(left)*f(right) ≤ 0.
    tol_sec — точность по времени (секунды UT).
    """
    fL = _f_phase(jd_left, target_deg)
    fR = _f_phase(jd_right, target_deg)
    if fL == 0.0: return jd_left
    if fR == 0.0: return jd_right
    if fL * fR > 0:
        raise ValueError("Phase root is not bracketed")

    tol_days = tol_sec / 86400.0
    a, b = jd_left, jd_right
    for _ in range(max_iter):
        m = 0.5 * (a + b)
        fM = _f_phase(m, target_deg)
        if abs(b - a) < tol_days or fM == 0.0:
            return m
        if fL * fM <= 0:
            b, fR = m, fM
        else:
            a, fL = m, fM
    return 0.5 * (a + b)

def _find_prev_lunation(jd_ut: float, kind: Literal["new","full"]) -> float:
    """
    Находит предыдущее событие заданного типа до jd_ut.
    kind="new"  -> Δλ≈0°
    kind="full" -> Δλ≈180°
    """
    target = 0.0 if kind == "new" else 180.0
    step = 0.5  # шагаем назад по 0.5 суток
    prev = jd_ut - step
    f_prev = _f_phase(prev, target)

    for _ in range(200):  # хватит с запасом
        cur = prev - step
        f_cur = _f_phase(cur, target)
        if f_prev == 0.0:
            return prev
        if f_prev * f_cur <= 0:
            # корень между cur..prev
            return _bisect_root(cur, prev, target)
        prev, f_prev = cur, f_cur

    # fallback: очень маловероятно сюда попасть
    return jd_ut - 29.5306

def _to_jd_utc(date: str, time: str, tz: str) -> float:
    dt_local = datetime.fromisoformat(f"{date}T{time}")
    z = ZoneInfo(tz)
    dt_utc = dt_local.replace(tzinfo=z).astimezone(ZoneInfo("UTC"))
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    )

def _jd_to_iso_utc(jd_ut: float) -> str:
    y,m,d,ut = swe.revjul(jd_ut, swe.GREG_CAL)
    hh = int(ut)
    mm = int((ut - hh) * 60)
    ss = int(round((((ut - hh) * 60) - mm) * 60))
    if ss == 60:
        ss = 0
        mm += 1
    return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d} UTC"

def _determine_san1_type_by_natal(sun_lon: float, moon_lon: float) -> Literal["new","full"]:
    """
    Если Луна в секторе (Солнце -> Солнце+180) => SAN1=new, иначе SAN1=full.
    """
    sun = _norm360(sun_lon)
    moon = _norm360(moon_lon)
    end_plus = (sun + 180.0) % 360.0
    if sun < end_plus:
        in_plus = (sun <= moon <= end_plus)
    else:
        in_plus = (moon >= sun or moon <= end_plus)
    return "new" if in_plus else "full"

def _pack(label: str, kind: Literal["new","full"], jd: float, jd_birth: float) -> Dict[str, Any]:
    mlon, slon = _moon_sun_longitudes(jd)
    delta = _angdiff(mlon, slon)  # (-180,180]
    target = 0.0 if kind == "new" else 180.0
    # нормируем delta для репорта:
    if kind == "new":
        drep = _norm360(delta)                # около 0
    else:
        drep = _norm360(delta - 180.0)        # около 0
    return {
        "label": label,
        "type": "NM" if kind == "new" else "FM",
        "typeName": "New Moon" if kind == "new" else "Full Moon",
        "datetime": _jd_to_iso_utc(jd),
        "jd_ut": jd,
        "sun_lon": _norm360(slon),
        "moon_lon": _norm360(mlon),
        "delta_deg": round(drep, 6),
        "delta_from_birth_days": round(jd_birth - jd, 6),
        "delta_from_birth_hours": round((jd_birth - jd) * 24.0, 2),
    }

def calc_prenatal_lunations(
    date: str, time: str, lat: float, lon: float, tz: str,
    *, natal_sun_lon: float | None = None, natal_moon_lon: float | None = None
) -> Dict[str, Any]:
    """
    SAN по правилу:
      1) SAN1 — тип выбирается по наталу:
         - Moon в секторе (Sun -> Sun+180) → SAN1=new
         - иначе → SAN1=full
      2) SAN1 — предыдущее до рождения лун. событие выбранного типа
      3) SAN2 — предыдущее до SAN1 событие противоположного типа
    Возвращает SAN1 и SAN2 с типом, временем, JD и долготами светил.
    """
    jd_birth = _to_jd_utc(date, time, tz)

    # Если долгот Солнца/Луны в натале не передали — посчитаем на лету (по UT)
    if natal_sun_lon is None or natal_moon_lon is None:
        mx, _ = swe.calc_ut(jd_birth, swe.MOON, swe.FLG_SWIEPH)
        sx, _ = swe.calc_ut(jd_birth, swe.SUN,  swe.FLG_SWIEPH)
        natal_moon_lon = _norm360(mx[0])
        natal_sun_lon  = _norm360(sx[0])

    san1_kind: Literal["new","full"] = _determine_san1_type_by_natal(natal_sun_lon, natal_moon_lon)
    san2_kind: Literal["new","full"] = "full" if san1_kind == "new" else "new"

    san1_jd = _find_prev_lunation(jd_birth, san1_kind)
    # небольшой сдвиг назад, чтобы гарантированно уйти левее san1 при поиске SAN2
    san2_jd = _find_prev_lunation(san1_jd - 1e-6, san2_kind)

    return {
        "SAN1": _pack("SAN1", san1_kind, san1_jd, jd_birth),
        "SAN2": _pack("SAN2", san2_kind, san2_jd, jd_birth),
    }