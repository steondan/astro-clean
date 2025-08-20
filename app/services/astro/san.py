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
    """Разность a-b в диапазоне (-180, 180]."""
    d = (a - b + 180.0) % 360.0 - 180.0
    return d


def _moon_sun_longitudes(jd_ut: float) -> Tuple[float, float]:
    """Геоцентрические тропические долготы Луны и Солнца в градусах."""
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


def _bisect_root(
    jd_left: float,
    jd_right: float,
    target_deg: float,
    max_iter: int = 50,
    tol_sec: float = 0.5
) -> float:
    """
    Бисекция корня f(jd)=sin(Δλ−target)=0 на [left,right]. Требует f(left)*f(right) ≤ 0.
    tol_sec — точность по времени (секунды UT).
    """
    fL = _f_phase(jd_left, target_deg)
    fR = _f_phase(jd_right, target_deg)
    if fL == 0.0:
        return jd_left
    if fR == 0.0:
        return jd_right
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


def _find_prev_lunation(jd_ut: float, kind: Literal["new", "full"]) -> float:
    """
    Находит предыдущее событие заданного типа до jd_ut.
    kind="new"  -> Δλ≈0°
    kind="full" -> Δλ≈180°
    """
    target = 0.0 if kind == "new" else 180.0

    # Шаг назад для грубого поиска (полдня) и разумный лимит (100 суток)
    step = 0.5  # дней
    limit_days = 100.0
    walked = 0.0

    prev = jd_ut - step
    f_prev = _f_phase(prev, target)

    # идём назад, пока не сменится знак или не упрёмся в лимит
    while walked < limit_days:
        cur = prev - step
        f_cur = _f_phase(cur, target)
        if f_prev == 0.0:
            return prev
        if f_prev * f_cur <= 0:
            # корень между cur..prev
            return _bisect_root(cur, prev, target)
        prev, f_prev = cur, f_cur
        walked += step

    # fallback (что практически не должно случаться)
    return jd_ut - 29.5306


def _parse_time_maybe_seconds(time_str: str) -> str:
    """Принимает 'HH:MM' или 'HH:MM:SS' и возвращает 'HH:MM:SS'."""
    parts = time_str.split(":")
    if len(parts) == 2:
        hh, mm = parts
        return f"{int(hh):02d}:{int(mm):02d}:00"
    elif len(parts) == 3:
        hh, mm, ss = parts
        return f"{int(hh):02d}:{int(mm):02d}:{int(ss):02d}"
    else:
        raise ValueError("time must be HH:MM or HH:MM:SS")


def _to_jd_utc(date: str, time: str, tz: str) -> float:
    time_norm = _parse_time_maybe_seconds(time)
    dt_local = datetime.fromisoformat(f"{date}T{time_norm}")
    z = ZoneInfo(tz)
    dt_utc = dt_local.replace(tzinfo=z).astimezone(ZoneInfo("UTC"))
    ut = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut)


def _jd_to_iso_utc(jd_ut: float) -> str:
    """Возвращает строку UTC 'YYYY-MM-DD HH:MM:SS UTC' c корректным округлением."""
    y, m, d, ut = swe.revjul(jd_ut, swe.GREG_CAL)
    total_sec = ut * 3600.0
    ss = int(round(total_sec % 60))
    mm = int((total_sec // 60) % 60)
    hh = int(total_sec // 3600)

    # Нормализация переполнений после округления секунд
    if ss == 60:
        ss = 0
        mm += 1
    if mm == 60:
        mm = 0
        hh += 1
    if hh == 24:
        # Перекат суток вперёд (редко, но корректно)
        jd_next = jd_ut + 1.0 / 86400.0  # +1 сек, пересчитаем чисто
        y, m, d, ut = swe.revjul(jd_next, swe.GREG_CAL)
        total_sec = ut * 3600.0
        ss = int(round(total_sec % 60))
        mm = int((total_sec // 60) % 60)
        hh = int(total_sec // 3600)

    return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d} UTC"


def calc_prenatal_lunations(
    date: str,
    time: str,
    lat: float,   # пока не используется (зарезервировано)
    lon: float,   # пока не используется (зарезервировано)
    tz: str
) -> Dict[str, Any]:
    """
    Возвращает две преднатальные сизигии до рождения:
      - SAN1: ближайшая назад (New/Full — что ближе)
      - SAN2: вторая назад противоположного типа
    Поля: label, type(NM/FM), typeName, datetime(UTC), jd_ut, sun_lon, moon_lon, delta_deg,
          delta_from_birth_days/hours.
    """
    jd_birth = _to_jd_utc(date, time, tz)

    jd_new  = _find_prev_lunation(jd_birth, "new")
    jd_full = _find_prev_lunation(jd_birth, "full")

    dist_new = abs(jd_birth - jd_new)
    dist_full = abs(jd_birth - jd_full)
    if dist_new <= dist_full:
        san1_type, san1_jd = "NM", jd_new
        san2_type, san2_jd = "FM", jd_full
    else:
        san1_type, san1_jd = "FM", jd_full
        san2_type, san2_jd = "NM", jd_new

    def pack(label: str, typ_code: str, jd: float) -> Dict[str, Any]:
        mlon, slon = _moon_sun_longitudes(jd)
        delta = _angdiff(mlon, slon)
        target = 0.0 if typ_code == "NM" else 180.0

        # для отчётности: насколько «в фазе» (близко к 0 или 180)
        delta_for_out = _norm360(delta) if typ_code == "NM" else _norm360(delta - 180.0)
        delta_days = jd_birth - jd
        return {
            "label": label,
            "type": typ_code,  # "NM" / "FM"
            "typeName": "New Moon" if typ_code == "NM" else "Full Moon",
            "datetime": _jd_to_iso_utc(jd),
            "jd_ut": jd,
            "sun_lon": _norm360(slon),
            "moon_lon": _norm360(mlon),
            "delta_deg": round(delta_for_out, 6),
            "delta_from_birth_days": round(delta_days, 6),
            "delta_from_birth_hours": round(delta_days * 24.0, 3),
        }

    return {
        "SAN1": pack("SAN1", san1_type, san1_jd),
        "SAN2": pack("SAN2", san2_type, san2_jd),
    }