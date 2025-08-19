import swisseph as swe

HOUSE_SYSTEMS = {
    "Placidus":   b'P',
    "Equal":      b'E',
    "WholeSign":  b'W',
    "Porphyry":   b'O',
    "Alcabitius": b'B',  # Alcabitius = 'B'
}
LOCK_ASC_MC = {b'P', b'B', b'O', b'E'}

def _norm360(x: float) -> float:
    x = x % 360.0
    return x + 360.0 if x < 0 else x

def _normalize_cusps(cusps_raw) -> list[float]:
    if len(cusps_raw) >= 13:
        arr = [_norm360(c) for c in cusps_raw[1:13]]
    elif len(cusps_raw) >= 12:
        arr = [_norm360(c) for c in cusps_raw[0:12]]
    else:
        arr = [_norm360(c) for c in cusps_raw] + [0.0] * (12 - len(cusps_raw))
    return arr[:12]

def _whole_sign_cusps_from_asc(asc: float) -> list[float]:
    start = 30.0 * int(asc // 30.0)
    return [_norm360(start + 30.0 * i) for i in range(12)]

def _get_angles(jd_ut: float, lat: float, lon: float):
    _, ascmc = swe.houses(jd_ut, float(lat), float(lon), b'P')
    ASC = _norm360(ascmc[0]); MC = _norm360(ascmc[1])
    DC = _norm360(ASC + 180.0); IC = _norm360(MC + 180.0)
    return ASC, MC, DC, IC

def calc_houses(jd_ut: float, lat: float, lon: float, system: str):
    sys_code = HOUSE_SYSTEMS.get(system)
    if sys_code is None:
        raise ValueError(f"Unknown house system: {system}")
    ASC, MC, DC, IC = _get_angles(jd_ut, lat, lon)
    if sys_code == b'W':
        cusps12 = _whole_sign_cusps_from_asc(ASC)
    else:
        cusps_raw, _ = swe.houses(jd_ut, float(lat), float(lon), sys_code)
        cusps12 = _normalize_cusps(cusps_raw)
        if sys_code in LOCK_ASC_MC:
            cusps12 = cusps12[:]
            cusps12[0] = ASC; cusps12[9] = MC; cusps12[6] = DC; cusps12[3] = IC
    cusps_obj = {str(i + 1): cusps12[i] for i in range(12)}
    angles = {"ASC": ASC, "MC": MC, "DC": DC, "IC": IC}
    return {"cusps": cusps_obj}, angles
