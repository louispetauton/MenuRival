from __future__ import annotations

import json
import logging
import re
from typing import Union, List
from anthropic import AsyncAnthropic
from bs4 import BeautifulSoup
from config import settings

logger = logging.getLogger(__name__)

CLIENT = AsyncAnthropic(api_key=settings.anthropic_api_key)
MODEL = "claude-sonnet-4-20250514"
MAX_TEXT_CHARS = 80_000

MENU_PARSE_PROMPT = """You are a menu data extraction agent. Extract ALL menu items from the provided content.
Return ONLY valid JSON, no markdown fences, no explanation, no preamble.

Required schema:
{
  "estimated_menu_date": "YYYY-MM-DD or null",
  "categories": [
    {
      "name": "Category Name",
      "items": [
        {
          "name": "Item Name",
          "description": "Full description or null",
          "price": 12.99,
          "price_notes": "per person / market price / null"
        }
      ]
    }
  ]
}

Rules:
- Return ONLY valid JSON, no markdown fences, no preamble
- Include every item visible including seasonal, limited, or sold-out items
- If price is a range, use the lower bound and put the full range in price_notes
- If an item has no price, set price to null
- Normalize category names (e.g. "Starters" -> "Appetizers")
- For estimated_menu_date: look for "last updated" text, copyright year, seasonal references, or any date clues
- If no menu items found, return: {"estimated_menu_date": null, "categories": []}"""

MENU_PARSE_PROMPT_VISION = """You are a menu data extraction agent. Extract ALL menu items from the provided menu image(s).
Return ONLY valid JSON, no markdown fences, no explanation, no preamble.

Required schema:
{
  "estimated_menu_date": "YYYY-MM-DD or null",
  "categories": [
    {
      "name": "Category Name",
      "items": [
        {
          "name": "Item Name",
          "description": "Full description or null",
          "price": 12.99,
          "price_notes": "per person / market price / null"
        }
      ]
    }
  ]
}

Rules:
- Return ONLY valid JSON, no markdown fences, no preamble
- Prices follow item names, often right-aligned or same line
- Section headers are usually capitalized or on their own line — treat as category names
- Ignore page numbers, logos, address, hours, decorative text
- If price is ambiguous, include item and explain in price_notes
- Two-column menus: read left column top-to-bottom, then right column
- If price is a range, use the lower bound and put the full range in price_notes
- If an item has no price, set price to null
- If no menu items found, return: {"estimated_menu_date": null, "categories": []}"""

RESTAURANT_META_PROMPT = """You are a restaurant data extraction agent. Extract restaurant metadata from the provided page content.
Return ONLY valid JSON, no markdown fences, no explanation, no preamble.

Required schema:
{
  "name": "Restaurant Name",
  "address": "Full address or null",
  "neighborhood": "Neighborhood name or null",
  "phone": "Phone number or null",
  "website_url": "URL or null",
  "cuisine_type": ["cuisine1", "cuisine2"],
  "google_stars": 4.2,
  "yelp_stars": 4.0
}

Rules:
- Return ONLY valid JSON
- google_stars: only populate if the page is a Google Maps or Google Search result; otherwise null
- yelp_stars: only populate if the page is a Yelp listing; otherwise null
- If a field is not found, use null
- cuisine_type should be an array of 1-3 strings describing the cuisine"""

STANDARDIZE_PROMPT = """You are a menu standardization agent. Map each raw menu item to a canonical name and category.
Return ONLY a valid JSON array, no preamble, no markdown fences.

Input: JSON array of menu items with id, name, description, price.
Output: JSON array with standardized fields.

Output schema:
[{"id": "uuid", "standardized_name": "Burger", "standardized_category": "Burger", "confidence": "high"}]

Valid standardized_category values (use EXACTLY these strings):
Appetizer | Salad | Soup | Pasta | Burger | Sandwich | Pizza | Seafood |
Meat | Poultry | Vegetarian | Side | Dessert | Cocktail | Wine | Beer |
Spirits | Non-Alcoholic | Breakfast | Brunch | Happy Hour | Tasting Menu

Rules:
- Return ONLY a valid JSON array, no preamble
- For ambiguous items, use the closest category and set confidence: "low"
- standardized_name should be a short canonical dish name (1-4 words, title case)
- Do not invent categories outside the list above
- Match each input id to its corresponding output id exactly"""

INSIGHT_PROMPT = """You are a restaurant pricing analyst. Write a concise benchmarking brief for the subject restaurant based on the provided data.
Return ONLY valid JSON, no markdown fences, no explanation, no preamble.

Output schema:
{
  "headline": "One sentence summary of pricing position",
  "pricing_position": "2-3 sentence paragraph describing where the subject sits in the market",
  "opportunities": ["Up to 3 actionable bullet strings referencing specific dishes and price differences"],
  "gaps": ["Category names that competitors offer but subject does not"]
}

Rules:
- Return ONLY valid JSON
- Be specific — reference actual dish names and price differences in dollars
- Opportunities should be actionable (e.g. "Raise the Classic Burger from $14 to $17 — competitors average $17.50")
- gaps should be category names the subject is missing entirely"""


def _strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "iframe"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def _parse_json_response(text: str) -> Union[dict, list]:
    text = text.strip()
    # Strip markdown fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def parse_menu_html(raw_html: str, restaurant_name: str) -> dict:
    text = _strip_html(raw_html)[:MAX_TEXT_CHARS]
    try:
        response = await CLIENT.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"{MENU_PARSE_PROMPT}\n\nRestaurant: {restaurant_name}\n\nContent:\n{text}"
            }]
        )
        return _parse_json_response(response.content[0].text)
    except Exception as e:
        logger.error(f"parse_menu_html error: {e}")
        return {"estimated_menu_date": None, "categories": []}


async def parse_restaurant_meta(raw_html: str) -> dict:
    text = _strip_html(raw_html)[:40_000]
    try:
        response = await CLIENT.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"{RESTAURANT_META_PROMPT}\n\nContent:\n{text}"
            }]
        )
        return _parse_json_response(response.content[0].text)
    except Exception as e:
        logger.error(f"parse_restaurant_meta error: {e}")
        return {}


async def standardize_items(items: List[dict]) -> List[dict]:
    batch_size = 50
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        try:
            response = await CLIENT.messages.create(
                model=MODEL,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": f"{STANDARDIZE_PROMPT}\n\nItems:\n{json.dumps(batch)}"
                }]
            )
            batch_results = _parse_json_response(response.content[0].text)
            if isinstance(batch_results, list):
                results.extend(batch_results)
        except Exception as e:
            logger.error(f"standardize_items batch {i} error: {e}")
    return results


async def generate_insight(subject: dict, competitor_data: dict) -> dict:
    payload = {
        "subject_restaurant": subject["name"],
        "subject_items": subject.get("items", []),
        "competitor_data": competitor_data
    }
    try:
        response = await CLIENT.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": f"{INSIGHT_PROMPT}\n\nData:\n{json.dumps(payload)}"
            }]
        )
        return _parse_json_response(response.content[0].text)
    except Exception as e:
        logger.error(f"generate_insight error: {e}")
        return {
            "headline": "Insight generation failed",
            "pricing_position": str(e),
            "opportunities": [],
            "gaps": []
        }
