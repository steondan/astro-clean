# app/services/astro/eclipses.py
from __future__ import annotations
from typing import List, Dict, Any
import swisseph as swe

def _jd_to_iso_utc(jd_ut: float) -> str:
    y, m, d, ut = swe.revjul(jd_ut, swe.GREG_CAL)
    hh = int(ut)
    mm = int((ut - hh) * 60)
    ss = int(round((((ut - hh) * 60) - mm) * 60))
    if ss == 60:
        ss = 0
        mm += 1
    return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d} UTC"

def _solar_type(retflag: int) -> str:
    # типы солнечных затмений
    if retflag & swe.SE_ECL_TOTAL:
        return "Total"
    if retflag & swe.SE_ECL_ANNULAR_TOTAL:
        return "Hybrid"
    if retflag & swe.SE_ECL_ANNULAR:
        return "Annular"
    if retflag & swe.SE_ECL_PARTIAL:
        return "Partial"
    return "Unknown"

def _lunar_type(retflag: int) -> str:
    # типы лунных затмений
    if retflag & swe.SE_ECL_TOTAL:
        return "Total"
    if retflag & swe.SE_ECL_PARTIAL:
        return "Partial"
    # Полн. константа для полутеневого (в pyswisseph обычно SE_ECL_PENUMBRAL)
    if hasattr(swe, "SE_ECL_PENUMBRAL") and (retflag & getattr(swe, "SE_ECL_PENUMBRAL")):
        return "Penumbral"
    return "Unknown"

def _next_solar(jd_start: float, count: int = 2) -> List[Dict[str, Any]]:
    """Глобальные ближайшие солнечные затмения после jd_start."""
    res: List[Dict[str, Any]] = []
    jd = jd_start
    for _ in range(count):
        try:
            # sol_eclipse_when_glob(jd, iflag, backw=0) -> (tret, retflag)
            tret, retflag = swe.sol_eclipse_when_glob(jd, swe.FLG_SWIEPH, 0)
        except Exception as e:
            res.append({"error": f"solar calc error: {e}"})
            break
        if not retflag:
            break
        # По SwissEph tret[0] — момент максимума
        tmax = float(tret[0])
        res.append({
            "type": _solar_type(retflag),
            "jd_ut": tmax,
            "datetime": _jd_to_iso_utc(tmax),
            "retflag": int(retflag),
        })
        jd = tmax + 1.0  # шагнём дальше, чтобы найти следующее
    return res

def _next_lunar(jd_start: float, count: int = 2) -> List[Dict[str, Any]]:
    """Глобальные ближайшие лунные затмения после jd_start."""
    res: List[Dict[str, Any]] = []
    jd = jd_start
    for _ in range(count):
        try:
            # lun_eclipse_when(jd, iflag, backw=0) -> (tret, retflag)
            tret, retflag = swe.lun_eclipse_when(jd, swe.FLG_SWIEPH, 0)
        except Exception as e:
            res.append({"error": f"lunar calc error: {e}"})
            break
        if not retflag:
            break
        tmax = float(tret[0])
        res.append({
            "type": _lunar_type(retflag),
            "jd_ut": tmax,
            "datetime": _jd_to_iso_utc(tmax),
            "retflag": int(retflag),
        })
        jd = tmax + 1.0
    return res

def calc_next_eclipses(jd_ut_start: float, count_each: int = 1) -> Dict[str, Any]:
    """
    Вернёт ближайшие (глобальные) затмения после jd_ut_start.
    count_each — сколько солнечных и лунных вернуть (по умолчанию по одному).
    """
    return {
        "solar": _next_solar(jd_ut_start, count=count_each),
        "lunar": _next_lunar(jd_ut_start, count=count_each),
    }