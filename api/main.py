import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from api.routers import restaurants, lookup, ingest, standardize, comparison

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MenuRival API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes under /api prefix
app.include_router(restaurants.router, prefix="/api")
app.include_router(lookup.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(standardize.router, prefix="/api")
app.include_router(comparison.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


@app.on_event("startup")
async def on_startup():
    try:
        from config import settings
        from supabase import create_client
        db = create_client(settings.supabase_url, settings.supabase_service_key)
        db.table("markets").select("id").limit(1).execute()
        logger.info("Supabase connection OK")
    except Exception as e:
        logger.warning(f"Supabase connection check failed: {e}")


# Serve frontend static files — must come after API routes
DIST = Path(__file__).parent.parent / "dashboard" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse(DIST / "index.html")
