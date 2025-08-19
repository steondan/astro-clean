from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

def ensure_datetime(date: str, time_str: str, tz: str | None, tz_offset_min: int | None):
    try:
        naive = datetime.fromisoformat(f"{date}T{time_str}")
    except Exception:
        raise HTTPException(400, detail="Invalid date/time. Use date=YYYY-MM-DD, time=HH:MM(:SS)")
    if tz and tz_offset_min is not None:
        raise HTTPException(400, detail="Provide either tz or tz_offset_min, not both.")
    if tz:
        try:
            z = ZoneInfo(tz)
        except Exception:
            raise HTTPException(400, detail=f"Unknown tz: {tz}")
        dt_local = naive.replace(tzinfo=z)
        tzname = tz
    elif tz_offset_min is not None:
        dt_local = naive.replace(tzinfo=timezone.utc) + timedelta(minutes=tz_offset_min)
        tzname = f"UTC{tz_offset_min/60:+.0f}"
    else:
        dt_local = naive.replace(tzinfo=timezone.utc)
        tzname = "UTC"
    dt_utc = dt_local.astimezone(timezone.utc)
    return dt_local, dt_utc, tzname
