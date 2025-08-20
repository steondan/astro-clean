# app/services/astro/stars.py
from __future__ import annotations
from typing import List, Dict, Any
import swisseph as swe

def _norm360(x: float) -> float:
    x %= 360.0
    return x + 360.0 if x < 0 else x

def calc_stars(jd_ut: float, star_names: List[str]) -> List[Dict[str, Any]]:
    """
    Расчёт фикс-звёзд по именам через Swiss Ephemeris.
    Требует наличия sefstars.txt в SE_EPHE_PATH.
    Возвращает массив записей по звёздам.
    """
    out: List[Dict[str, Any]] = []
    # Флаги: швейцарские эфемериды + скорости (если есть)
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED

    for raw in star_names:
        name_q = raw.strip()
        if not name_q:
            continue
        try:
            # Примеры допустимых имён: "Sirius", "Regulus", "Spica", "alCMa" и т.п.
            resolved_name, xx, rf = swe.fixstar_ut(name_q, jd_ut, flags)
            # xx: [lon, lat, dist, lon_speed, lat_speed, dist_speed]
            rec: Dict[str, Any] = {
                "input": name_q,
                "name": resolved_name.strip() if isinstance(resolved_name, str) else str(resolved_name),
                "lon": _norm360(float(xx[0])),
                "lat": float(xx[1]),
            }
            # Скорости могут быть NaN/не нужны — добавляем, только если есть числа
            try:
                lon_spd = float(xx[3])
                lat_spd = float(xx[4])
                if lon_spd == lon_spd:  # not NaN
                    rec["lon_speed"] = lon_spd
                if lat_spd == lat_spd:
                    rec["lat_speed"] = lat_spd
            except Exception:
                pass

            out.append(rec)
        except Exception as e:
            out.append({
                "input": name_q,
                "error": str(e),
            })

    return out