import re
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from api.models import RestaurantCreate, RestaurantUpdate, RestaurantResponse
from config import settings
from supabase import create_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/restaurants", tags=["restaurants"])


def get_db():
    return create_client(settings.supabase_url, settings.supabase_service_key)


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = re.sub(r"^-+|-+$", "", slug)
    return slug


@router.get("", response_model=list[RestaurantResponse])
async def list_restaurants():
    db = get_db()
    res = db.table("restaurants").select("*").order("is_subject", desc=True).order("name").execute()
    restaurants = res.data or []
    result = []
    for r in restaurants:
        count_res = db.table("menu_items").select("id", count="exact").eq("restaurant_id", r["id"]).execute()
        r["item_count"] = count_res.count or 0
        result.append(r)
    return result


@router.post("", response_model=RestaurantResponse, status_code=201)
async def create_restaurant(body: RestaurantCreate):
    db = get_db()
    count_res = db.table("restaurants").select("id", count="exact").execute()
    if (count_res.count or 0) >= 10:
        raise HTTPException(status_code=400, detail="Maximum of 10 restaurants reached.")

    # Get SF market id if not provided
    market_id = body.market_id
    if not market_id:
        mkt = db.table("markets").select("id").eq("slug", "sf").execute()
        if mkt.data:
            market_id = mkt.data[0]["id"]

    slug = body.slug or slugify(body.name)
    # Make slug unique
    existing = db.table("restaurants").select("slug").like("slug", f"{slug}%").execute()
    existing_slugs = {r["slug"] for r in (existing.data or [])}
    if slug in existing_slugs:
        i = 2
        while f"{slug}-{i}" in existing_slugs:
            i += 1
        slug = f"{slug}-{i}"

    data = body.model_dump(exclude={"market_id", "slug"})
    data["slug"] = slug
    data["market_id"] = market_id

    res = db.table("restaurants").insert(data).execute()
    r = res.data[0]
    r["item_count"] = 0
    return r


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(restaurant_id: str, body: RestaurantUpdate):
    db = get_db()
    existing = db.table("restaurants").select("*").eq("id", restaurant_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    update_data = body.model_dump(exclude_none=True)

    if update_data.get("is_subject") is True:
        # Un-subject all others first
        db.table("restaurants").update({"is_subject": False}).neq("id", restaurant_id).execute()

    res = db.table("restaurants").update(update_data).eq("id", restaurant_id).execute()
    r = res.data[0]
    count_res = db.table("menu_items").select("id", count="exact").eq("restaurant_id", restaurant_id).execute()
    r["item_count"] = count_res.count or 0
    return r


@router.delete("/{restaurant_id}", status_code=204)
async def delete_restaurant(restaurant_id: str):
    db = get_db()
    existing = db.table("restaurants").select("id").eq("id", restaurant_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Restaurant not found.")
    db.table("restaurants").delete().eq("id", restaurant_id).execute()


@router.get("/{restaurant_id}/menu-items")
async def get_menu_items(
    restaurant_id: str,
    menu_type: Optional[str] = None,
    standardized_only: bool = False
):
    db = get_db()
    query = db.table("menu_items").select("*").eq("restaurant_id", restaurant_id)
    if menu_type:
        query = query.eq("menu_type", menu_type)
    if standardized_only:
        query = query.not_.is_("standardized_name", "null")
    res = query.execute()
    return res.data or []
