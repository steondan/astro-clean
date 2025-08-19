from fastapi import APIRouter, Query, HTTPException
from ..services.geo import ensure_datetime
from ..services.astro import calc_chart

router = APIRouter()

@router.get("/")
def chart(
    date: str = Query(..., example="1971-06-22"),
    time: str = Query(..., example="02:30:00"),
    lat: float = Query(..., example=59.4167),
    lon: float = Query(..., example=24.75),
    tz: str | None = Query("UTC", example="Europe/Tallinn"),
    tz_offset_min: int | None = Query(None),
    houseSystem: str = Query("Placidus", description="Placidus/Alcabitius/Porphyry/Equal/WholeSign"),
    nodes: str = Query("mean", pattern="^(mean|true|false|True|False)$"),
    stars: str | None = Query(None),
    detail: bool = Query(True)
):
    try:
        dt_local, dt_utc, tzname = ensure_datetime(date, time, tz, tz_offset_min)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=f"Bad datetime: {e}")

    star_list = [s.strip() for s in stars.split(",")] if stars else None

    try:
        bodies, houses, angles, engine, extras = calc_chart(
            dt_utc, lat, lon, nodes, houseSystem, detail=detail, stars=star_list, eclipses=False
        )
    except Exception as e:
        raise HTTPException(400, detail=f"Calc error: {e}")

    return {
        "time": {"datetimeLocal": dt_local.isoformat(), "datetimeUTC": dt_utc.isoformat(), "tz": tzname},
        "location": {"lat": lat, "lon": lon},
        "settings": {"engine": engine, "houseSystem": houseSystem, "nodes": nodes, "detail": detail},
        "bodies": bodies,
        "houses": houses,   # {"cusps": {"1":..,"2":..}}
        "angles": angles,
        "extras": extras
    }
