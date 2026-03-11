import logging
from fastapi import APIRouter, HTTPException
from api.models import InsightResponse, GenerateInsightRequest
from config import settings
from ingestion.parser import generate_insight
from supabase import create_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["comparison"])


def get_db():
    return create_client(settings.supabase_url, settings.supabase_service_key)


@router.get("/comparison/category/{category}")
async def get_category_comparison(category: str):
    db = get_db()
    items_res = db.table("menu_items").select(
        "id,restaurant_id,name,standardized_name,standardized_category,price"
    ).eq("standardized_category", category).not_.is_("price", "null").execute()
    items = items_res.data or []

    if not items:
        return {"category": category, "items": []}

    # Get restaurant info
    rest_ids = list({i["restaurant_id"] for i in items})
    rests_res = db.table("restaurants").select("id,name,is_subject").in_("id", rest_ids).execute()
    rest_map = {r["id"]: r for r in (rests_res.data or [])}

    # Sort by price ascending
    items_sorted = sorted(items, key=lambda x: x.get("price") or 0)
    total = len(items_sorted)

    result_items = []
    for i, item in enumerate(items_sorted):
        rank = i + 1
        rest = rest_map.get(item["restaurant_id"], {})
        if rank == 1:
            position = "Cheapest"
        elif rank == total:
            position = "Most Expensive"
        else:
            position = f"{rank} of {total}"

        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, str(rank))
        result_items.append({
            "rank": rank,
            "rank_label": medal,
            "restaurant_name": rest.get("name", "Unknown"),
            "restaurant_id": item["restaurant_id"],
            "item_name": item.get("name"),
            "standardized_name": item.get("standardized_name"),
            "price": item.get("price"),
            "percentile_label": position,
            "is_subject": rest.get("is_subject", False),
        })

    return {"category": category, "items": result_items}


@router.get("/comparison/categories")
async def get_available_categories():
    """Return categories that have items from 2+ restaurants."""
    db = get_db()
    items_res = db.table("menu_items").select(
        "standardized_category,restaurant_id"
    ).not_.is_("standardized_category", "null").not_.is_("price", "null").execute()
    items = items_res.data or []

    cat_rests: dict[str, set] = {}
    for item in items:
        cat = item["standardized_category"]
        if cat not in cat_rests:
            cat_rests[cat] = set()
        cat_rests[cat].add(item["restaurant_id"])

    result = []
    for cat, rests in cat_rests.items():
        if len(rests) >= 2:
            result.append({"category": cat, "restaurant_count": len(rests)})

    return sorted(result, key=lambda x: x["category"])


@router.post("/insights/generate", response_model=InsightResponse)
async def generate_insights(body: GenerateInsightRequest):
    db = get_db()
    subject_id = body.subject_restaurant_id

    # Get subject restaurant
    sub_res = db.table("restaurants").select("*").eq("id", subject_id).execute()
    if not sub_res.data:
        raise HTTPException(status_code=404, detail="Subject restaurant not found.")
    subject = sub_res.data[0]

    # Get subject items (standardized only)
    sub_items_res = db.table("menu_items").select(
        "name,standardized_name,standardized_category,price"
    ).eq("restaurant_id", subject_id).not_.is_("standardized_name", "null").execute()
    subject["items"] = sub_items_res.data or []

    # Get competitor data per category
    all_items_res = db.table("menu_items").select(
        "restaurant_id,name,standardized_name,standardized_category,price"
    ).not_.is_("standardized_name", "null").not_.is_("price", "null").neq("restaurant_id", subject_id).execute()
    all_items = all_items_res.data or []

    rest_ids = list({i["restaurant_id"] for i in all_items})
    rests_res = db.table("restaurants").select("id,name").in_("id", rest_ids).execute()
    rest_map = {r["id"]: r["name"] for r in (rests_res.data or [])}

    competitor_data: dict = {}
    for item in all_items:
        cat = item.get("standardized_category")
        if not cat:
            continue
        if cat not in competitor_data:
            competitor_data[cat] = []
        competitor_data[cat].append({
            "restaurant_name": rest_map.get(item["restaurant_id"], "Unknown"),
            "item_name": item.get("name"),
            "price": item.get("price"),
        })

    insight_dict = await generate_insight(subject, competitor_data)

    save_res = db.table("insights").insert({
        "subject_restaurant_id": subject_id,
        "headline": insight_dict.get("headline"),
        "pricing_position": insight_dict.get("pricing_position"),
        "opportunities": insight_dict.get("opportunities"),
        "gaps": insight_dict.get("gaps"),
        "raw_response": str(insight_dict),
    }).execute()

    row = save_res.data[0]
    return InsightResponse(
        id=row["id"],
        headline=row.get("headline"),
        pricing_position=row.get("pricing_position"),
        opportunities=row.get("opportunities") or [],
        gaps=row.get("gaps") or [],
        date_generated=row["date_generated"],
    )


@router.get("/insights/latest", response_model=InsightResponse)
async def get_latest_insight(subject_restaurant_id: str):
    db = get_db()
    res = db.table("insights").select("*").eq(
        "subject_restaurant_id", subject_restaurant_id
    ).order("date_generated", desc=True).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="No insights found.")
    row = res.data[0]
    return InsightResponse(
        id=row["id"],
        headline=row.get("headline"),
        pricing_position=row.get("pricing_position"),
        opportunities=row.get("opportunities") or [],
        gaps=row.get("gaps") or [],
        date_generated=row["date_generated"],
    )
