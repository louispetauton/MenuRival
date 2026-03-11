import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

app.include_router(restaurants.router)
app.include_router(lookup.router)
app.include_router(ingest.router)
app.include_router(standardize.router)
app.include_router(comparison.router)


@app.get("/health")
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
