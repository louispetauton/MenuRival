import logging
from fastapi import APIRouter, HTTPException
from api.models import URLLookupRequest, URLLookupResponse
from ingestion.scraper import fetch_url, ScraperError
from ingestion.parser import parse_restaurant_meta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lookup", tags=["lookup"])


@router.post("/url", response_model=URLLookupResponse)
async def lookup_url(body: URLLookupRequest):
    try:
        html = await fetch_url(body.url)
    except ScraperError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"lookup_url scrape error: {e}")
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(e)}")
    try:
        meta = await parse_restaurant_meta(html)
    except Exception as e:
        logger.error(f"lookup_url parse error: {e}")
        raise HTTPException(status_code=500, detail=f"Parse failed: {str(e)}")
    return URLLookupResponse(**{
        "name": meta.get("name"),
        "address": meta.get("address"),
        "neighborhood": meta.get("neighborhood"),
        "phone": meta.get("phone"),
        "website_url": meta.get("website_url"),
        "cuisine_type": meta.get("cuisine_type", []),
        "google_stars": meta.get("google_stars"),
        "yelp_stars": meta.get("yelp_stars"),
    })
