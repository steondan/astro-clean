# app/main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers import natal

API_KEY = os.getenv("API_KEY", "dev-secret")

app = FastAPI(title="Astro API")

# Открытые пути (без API-ключа)
OPEN_PATHS = {"/health"}

@app.middleware("http")
async def check_api_key(request: Request, call_next):
    if request.url.path in OPEN_PATHS:
        return await call_next(request)
    key = (
        request.headers.get("x-api-key")
        or request.query_params.get("token")
        or request.query_params.get("api_key")
    )
    if key != API_KEY:
        return JSONResponse(status_code=403, content={"detail": "Forbidden: invalid or missing API key"})
    return await call_next(request)

@app.get("/health")
def health():
    return {"status": "ok"}

# Подключаем РОУТЕР НАТАЛЬНОЙ КАРТЫ
app.include_router(natal.router)