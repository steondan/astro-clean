import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import chart

app = FastAPI(title="Astro API (calc only)")

# API key from env; if empty => protection disabled (handy for local dev)
API_KEY = os.getenv("API_KEY", "").strip()

# Allow CORS (adjust later if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXEMPT_PATHS = {"/", "/health", "/favicon.ico", "/docs", "/redoc", "/openapi.json"}

@app.middleware("http")
async def api_key_guard(request: Request, call_next):
    if not API_KEY:
        return await call_next(request)
    if request.url.path in EXEMPT_PATHS:
        return await call_next(request)

    token = request.headers.get("x-api-key") or request.query_params.get("token") \
            or request.headers.get("X-API-Key") or request.query_params.get("api_key")

    if token != API_KEY:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    return await call_next(request)

@app.get("/health")
def health():
    return {"ok": True}

# Mount chart router at /chart
app.include_router(chart.router, prefix="/chart", tags=["chart"])
