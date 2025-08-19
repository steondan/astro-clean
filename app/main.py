import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.services.astro import calc_chart

app = FastAPI(title="Astro Calculator API")

# API key из переменных окружения
API_KEY = os.getenv("API_KEY", "").strip()

# Пути, где защита не нужна
EXEMPT_PATHS = {
    "/",
    "/health",
    "/favicon.ico",
    "/docs",
    "/redoc",
    "/openapi.json"
}

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Если ключ не настроен — пропускаем всех (локальная разработка)
    if not API_KEY:
        return await call_next(request)

    # Если путь в белом списке — пропускаем
    if request.url.path in EXEMPT_PATHS:
        return await call_next(request)

    # Проверяем заголовок x-api-key
    header_key = request.headers.get("x-api-key")
    # Или query-параметр ?token=...
    query_key = request.query_params.get("token")

    if header_key == API_KEY or query_key == API_KEY:
        return await call_next(request)

    return JSONResponse(
        status_code=403,
        content={"detail": "Forbidden: missing or invalid API key"}
    )

@app.get("/")
def root():
    return {"message": "Astro API running"}

@app.get("/health")
def health():
    return {"ok": True, "authEnabled": bool(API_KEY)}

@app.get("/chart/")
def chart(
    date: str,
    time: str,
    lat: float,
    lon: float,
    tz: str = "UTC",
    houseSystem: str = "Placidus",
    nodes: str = "mean",
    stars: str = None,
    detail: bool = False
):
    try:
        bodies, houses, angles, provider, _ = calc_chart(
            date, time, lat, lon, tz, houseSystem, nodes, stars, detail
        )
        return {
            "bodies": bodies,
            "houses": houses,
            "angles": angles,
            "provider": provider,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calc error: {e}")
