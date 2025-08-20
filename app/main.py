# app/main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers import natal

app = FastAPI(title="Astro API")

app.include_router(natal.router)

API_KEY = os.getenv("API_KEY")  # None -> отключаем проверку локально

EXEMPT_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

@app.get("/")
def root():
    return {"ok": True, "service": "Astro API"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.middleware("http")
async def api_key_guard(request: Request, call_next):
    # Разрешаем preflight и публичные пути
    if request.method == "OPTIONS" or request.url.path in EXEMPT_PATHS:
        return await call_next(request)

    # Если переменная API_KEY не задана — пропускаем (локалка)
    if not API_KEY:
        return await call_next(request)

    # Достаём ключ
    qp = request.query_params
    provided = (
        request.headers.get("x-api-key")
        or qp.get("token")
        or qp.get("api_key")
    )

    if provided != API_KEY:
        return JSONResponse(status_code=403, content={"detail": "Forbidden: invalid or missing API key"})

    return await call_next(request)