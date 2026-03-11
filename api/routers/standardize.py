import time
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from api.models import StandardizeResponse
from config import settings
from ingestion.parser import standardize_items
from supabase import create_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/standardize", tags=["standardize"])


class StandardizeRequest(BaseModel):
    restaurant_id: Optional[str] = None


def get_db():
    return create_client(settings.supabase_url, settings.supabase_service_key)


@router.post("/run", response_model=StandardizeResponse)
async def run_standardization(body: StandardizeRequest = StandardizeRequest()):
    db = get_db()
    t0 = time.time()

    query = db.table("menu_items").select("id,name,description,price").is_("standardized_name", "null")
    if body.restaurant_id:
        query = query.eq("restaurant_id", body.restaurant_id)
    res = query.execute()
    items = res.data or []

    if not items:
        return StandardizeResponse(
            total_processed=0,
            total_updated=0,
            duration_seconds=round(time.time() - t0, 2),
            message="No unstandardized items found."
        )

    results = await standardize_items([
        {"id": i["id"], "name": i["name"], "description": i.get("description"), "price": i.get("price")}
        for i in items
    ])

    updated = 0
    for r in results:
        try:
            db.table("menu_items").update({
                "standardized_name": r.get("standardized_name"),
                "standardized_category": r.get("standardized_category"),
                "confidence": r.get("confidence"),
            }).eq("id", r["id"]).execute()
            updated += 1

            # Upsert into standardized_items
            canon = r.get("standardized_name")
            cat = r.get("standardized_category")
            if canon and cat:
                # Find original name
                orig = next((i["name"] for i in items if i["id"] == r["id"]), None)
                existing = db.table("standardized_items").select("*").eq("canonical_name", canon).eq("category", cat).execute()
                if existing.data:
                    row = existing.data[0]
                    new_examples = list(set((row.get("example_raw_names") or []) + ([orig] if orig else [])))
                    db.table("standardized_items").update({
                        "item_count": (row.get("item_count") or 0) + 1,
                        "example_raw_names": new_examples,
                        "last_updated_at": "now()",
                    }).eq("id", row["id"]).execute()
                else:
                    db.table("standardized_items").insert({
                        "canonical_name": canon,
                        "category": cat,
                        "item_count": 1,
                        "example_raw_names": [orig] if orig else [],
                    }).execute()
        except Exception as e:
            logger.error(f"standardize update error for {r.get('id')}: {e}")

    return StandardizeResponse(
        total_processed=len(items),
        total_updated=updated,
        duration_seconds=round(time.time() - t0, 2),
        message=f"Standardized {updated} of {len(items)} items."
    )


@router.get("/status")
async def standardize_status():
    db = get_db()
    unstd = db.table("menu_items").select("id", count="exact").is_("standardized_name", "null").execute()
    std = db.table("menu_items").select("id", count="exact").not_.is_("standardized_name", "null").execute()

    cats_res = db.table("menu_items").select("standardized_category").not_.is_("standardized_category", "null").execute()
    cat_counts: dict[str, int] = {}
    for row in (cats_res.data or []):
        c = row["standardized_category"]
        cat_counts[c] = cat_counts.get(c, 0) + 1

    return {
        "unstandardized_count": unstd.count or 0,
        "standardized_count": std.count or 0,
        "categories": [{"name": k, "count": v} for k, v in sorted(cat_counts.items())]
    }
