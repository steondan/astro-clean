# app/services/astro/stars.py
from __future__ import annotations
from typing import List, Dict, Any, Union, Optional, Tuple
import swisseph as swe

def _norm360(x: float) -> float:
    x %= 360.0
    return x + 360.0 if x < 0 else x

def _parse_star_list(stars: Optional[Union[str, List[str]]]) -> List[str]:
    if stars is None:
        return []
    if isinstance(stars, list):
        return [s.strip() for s in stars if isinstance(s, str) and s.strip()]
    if isinstance(stars, str):
        return [s.strip() for s in stars.split(",") if s.strip()]
    raise ValueError("stars must be a comma-separated string or a list of strings")

def _unpack_fixstar_tuple(t: Tuple[Any, ...]) -> Tuple[str, List[float], int]:
    """
    Унифицируем разные возможные формы ответа:
      - (name:str, xx:(...floats...), retflag:int)
      - иногда порядок/типы могут меняться — разруливаем по типам.
    Возвращаем кортеж (resolved_name, xx_list, retflag_int) или бросаем исключение.
    """
    if not isinstance(t, (tuple, list)) or len(t) < 2:
        raise ValueError(f"unexpected return: {t!r}")

    name: Optional[str] = None
    xx: Optional[List[float]] = None
    retflag: int = 0

    # Кандидаты по типам
    for item in t:
        if isinstance(item, str) and name is None:
            name = item
        elif isinstance(item, (list, tuple)) and xx is None and len(item) >= 2:
            xx = list(item)
        elif isinstance(item, (int,)) and retflag == 0:
            retflag = int(item)

    if name is None or xx is None:
        raise ValueError(f"cannot unpack (name, xx, retflag) from {t!r}")
    return name, xx, retflag

def _try_fixstar2_ut(name: str, jd_ut: float):
    return _unpack_fixstar_tuple(swe.fixstar2_ut(name, jd_ut, swe.FLG_SWIEPH))

def _try_fixstar2_tt(name: str, jd_ut: float):
    jd_et = jd_ut + swe.deltat(jd_ut)
    return _unpack_fixstar_tuple(swe.fixstar2(name, jd_et, swe.FLG_SWIEPH))

def calc_stars(jd_ut: float, stars: Optional[Union[str, List[str]]]) -> List[Dict[str, Any]]:
    """
    Возвращает список рассчитанных звёзд (эклиптическая долгота/широта) или ошибки по каждой.
    Используем fixstar2_ut/fixstar2, т.к. они стабильнее по сигнатуре.
    """
    names = _parse_star_list(stars)
    out: List[Dict[str, Any]] = []

    for raw in names:
        name = (raw or "").strip()
        if not name:
            continue

        tried_errors: List[str] = []
        result: Optional[Tuple[str, List[float], int]] = None

        # 1) fixstar2_ut
        try:
            result = _try_fixstar2_ut(name, jd_ut)
        except Exception as e1:
            tried_errors.append(f"fixstar2_ut: {e1!s}")
            # 1a) «очистим» имя от не-ascii
            try:
                cleaned = name.encode("ascii", "ignore").decode()
                if cleaned and cleaned != name:
                    result = _try_fixstar2_ut(cleaned, jd_ut)
            except Exception as e1a:
                tried_errors.append(f"fixstar2_ut(cleaned): {e1a!s}")

        # 2) TT-версия
        if result is None:
            try:
                result = _try_fixstar2_tt(name, jd_ut)
            except Exception as e2:
                tried_errors.append(f"fixstar2(TT): {e2!s}")
                try:
                    cleaned = name.encode("ascii", "ignore").decode()
                    if cleaned and cleaned != name:
                        result = _try_fixstar2_tt(cleaned, jd_ut)
                except Exception as e2a:
                    tried_errors.append(f"fixstar2(TT, cleaned): {e2a!s}")

        if result is None:
            out.append({
                "name": name,
                "error": "; ".join(tried_errors) if tried_errors else "unknown error"
            })
            continue

        resolved, xx, rf = result
        try:
            lon = _norm360(float(xx[0]))
            lat = float(xx[1])
            out.append({
                "name": resolved or name,
                "lon": lon,
                "lat": lat,
                "retflag": int(rf),
                "engine": "Swiss Ephemeris"
            })
        except Exception as e:
            out.append({
                "name": name,
                "error": f"unexpected data format: {e}"
            })

    return out