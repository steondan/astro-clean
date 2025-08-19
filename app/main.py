from fastapi import FastAPI
from .routers import chart

app = FastAPI(title="Astro API (calc only)")
app.include_router(chart.router, prefix="/chart", tags=["chart"])

@app.get("/")
def root():
    return {"status": "ok", "service": "astro-calc"}
