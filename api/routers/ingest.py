import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from api.models import MenuUploadResponse, IngestURLRequest
from config import settings
from ingestion.scraper import fetch_url, ScraperError
from ingestion.parser import parse_menu_html, MODEL
from ingestion.vision_parser import parse_menu_photo
from supabase import create_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])


def get_db():
    return create_client(settings.supabase_url, settings.supabase_service_key)


def _detect_mime(filename: str, content_type: str) -> str:
    fn = filename.lower()
    if fn.endswith(".pdf"):
        return "application/pdf"
    elif fn.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    elif fn.endswith(".png"):
        return "image/png"
    elif fn.endswith(".webp"):
        return "image/webp"
    return content_type or "image/jpeg"


async def _save_items(db, pull_id: str, restaurant_id: str, menu_type: str, parsed: dict) -> int:
    items_to_insert = []
    for cat in parsed.get("categories", []):
        for item in cat.get("items", []):
            items_to_insert.append({
                "restaurant_id": restaurant_id,
                "pull_id": pull_id,
                "menu_type": menu_type,
                "name": item.get("name"),
                "description": item.get("description"),
                "price": item.get("price"),
                "price_notes": item.get("price_notes"),
                "category": cat.get("name"),
            })
    if items_to_insert:
        db.table("menu_items").insert(items_to_insert).execute()
    return len(items_to_insert)


@router.post("/photo", response_model=MenuUploadResponse)
async def ingest_photo(
    restaurant_id: str = Form(...),
    menu_type: str = Form("unknown"),
    file: UploadFile = File(...)
):
    db = get_db()
    rest = db.table("restaurants").select("id").eq("id", restaurant_id).execute()
    if not rest.data:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    file_bytes = await file.read()
    mime_type = _detect_mime(file.filename or "", file.content_type or "")

    try:
        parsed = await parse_menu_photo(file_bytes, mime_type, "")
        parse_status = "success"
    except Exception as e:
        logger.error(f"ingest_photo parse error: {e}")
        parsed = {"estimated_menu_date": None, "categories": []}
        parse_status = "failed"

    item_count = sum(len(c.get("items", [])) for c in parsed.get("categories", []))
    pull_res = db.table("menu_pulls").insert({
        "restaurant_id": restaurant_id,
        "menu_type": menu_type,
        "source": "photo_upload",
        "parse_status": parse_status,
        "item_count": item_count,
        "model_used": MODEL,
    }).execute()
    pull_id = pull_res.data[0]["id"]

    if parse_status == "success":
        await _save_items(db, pull_id, restaurant_id, menu_type, parsed)

    categories = [c["name"] for c in parsed.get("categories", [])]
    return MenuUploadResponse(
        pull_id=pull_id,
        restaurant_id=restaurant_id,
        menu_type=menu_type,
        item_count=item_count,
        parse_status=parse_status,
        categories=categories,
    )


@router.post("/url", response_model=MenuUploadResponse)
async def ingest_url(body: IngestURLRequest):
    db = get_db()
    rest = db.table("restaurants").select("id,name").eq("id", body.restaurant_id).execute()
    if not rest.data:
        raise HTTPException(status_code=404, detail="Restaurant not found.")
    restaurant_name = rest.data[0]["name"]

    try:
        html = await fetch_url(body.url)
    except ScraperError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(e)}")

    try:
        parsed = await parse_menu_html(html, restaurant_name)
        parse_status = "success"
    except Exception as e:
        logger.error(f"ingest_url parse error: {e}")
        parsed = {"estimated_menu_date": None, "categories": []}
        parse_status = "failed"

    item_count = sum(len(c.get("items", [])) for c in parsed.get("categories", []))
    pull_res = db.table("menu_pulls").insert({
        "restaurant_id": body.restaurant_id,
        "menu_type": body.menu_type,
        "source": "url_scrape",
        "source_url": body.url,
        "raw_content": html[:50_000],
        "parse_status": parse_status,
        "item_count": item_count,
        "model_used": MODEL,
    }).execute()
    pull_id = pull_res.data[0]["id"]

    if parse_status == "success":
        await _save_items(db, pull_id, body.restaurant_id, body.menu_type, parsed)

    categories = [c["name"] for c in parsed.get("categories", [])]
    return MenuUploadResponse(
        pull_id=pull_id,
        restaurant_id=body.restaurant_id,
        menu_type=body.menu_type,
        item_count=item_count,
        parse_status=parse_status,
        categories=categories,
    )
