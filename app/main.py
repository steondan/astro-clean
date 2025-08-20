# app/main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers import natal

API_KEY = os.getenv("API_KEY", "dev-secret")

app = FastAPI(title="Astro API")

# Разрешаем без ключа:
OPEN_PATHS = {
    "/", "/health",               # корень и health для Render
    "/docs", "/openapi.json",     # удобство при отладке
    "/redoc",
}

@app.middleware("http")
async def check_api_key(request: Request, call_next):
    # пропускаем OPTIONS (CORS/preflight)
    if request.method == "OPTIONS":
        return await call_next(request)

    # пропускаем открытые пути и их сабресурсы (например, /docs/*)
    path = request.url.path
    if path in OPEN_PATHS or any(path.startswith(p + "/") for p in OPEN_PATHS if p not in {"/"}):
        return await call_next(request)

    key = (
        request.headers.get("x-api-key")
        or request.query_params.get("token")
        or request.query_params.get("api_key")
    )
    if key != API_KEY:
        return JSONResponse(status_code=403, content={"detail": "Forbidden: invalid or missing API key"})
    return await call_next(request)

@app.get("/")
def root():
    return {"ok": True, "msg": "Astro API", "use": "/natal/chart"}

@app.get("/health")
def health():
    return {"status": "ok"}

# Натальный роутер
app.include_router(natal.router)