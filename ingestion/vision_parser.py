import logging
import base64
from ingestion.parser import CLIENT, MODEL, MENU_PARSE_PROMPT_VISION, _parse_json_response

logger = logging.getLogger(__name__)


def _pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> list[bytes]:
    import fitz  # pymupdf
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        images.append(pix.tobytes("jpeg"))
    doc.close()
    return images


def _merge_results(results: list[dict]) -> dict:
    merged_categories: dict[str, dict] = {}
    estimated_date = None
    for result in results:
        if result.get("estimated_menu_date") and not estimated_date:
            estimated_date = result["estimated_menu_date"]
        for cat in result.get("categories", []):
            cat_key = cat["name"].lower().strip()
            if cat_key not in merged_categories:
                merged_categories[cat_key] = {"name": cat["name"], "items": []}
            existing_names = {i["name"].lower() for i in merged_categories[cat_key]["items"]}
            for item in cat.get("items", []):
                if item["name"].lower() not in existing_names:
                    merged_categories[cat_key]["items"].append(item)
                    existing_names.add(item["name"].lower())
    return {
        "estimated_menu_date": estimated_date,
        "categories": list(merged_categories.values())
    }


async def _call_vision(image_list: list[bytes], restaurant_name: str) -> dict:
    content = [{"type": "text", "text": f"{MENU_PARSE_PROMPT_VISION}\n\nRestaurant: {restaurant_name}"}]
    for img_bytes in image_list:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": base64.b64encode(img_bytes).decode()
            }
        })
    response = await CLIENT.messages.create(
        model=MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": content}]
    )
    return _parse_json_response(response.content[0].text)


async def parse_menu_pdf(pdf_bytes: bytes, restaurant_name: str) -> dict:
    images = _pdf_to_images(pdf_bytes)
    page_count = len(images)
    print(f"PDF has {page_count} pages")

    results = []
    if page_count <= 20:
        result = await _call_vision(images, restaurant_name)
        results.append(result)
    else:
        for i in range(0, page_count, 5):
            batch = images[i:i + 5]
            result = await _call_vision(batch, restaurant_name)
            results.append(result)

    merged = _merge_results(results)
    item_count = sum(len(cat["items"]) for cat in merged.get("categories", []))
    print(f"Parsed {item_count} items from {page_count} pages")
    return merged


async def parse_menu_photo(image_bytes: bytes, mime_type: str, restaurant_name: str) -> dict:
    if mime_type == "application/pdf":
        return await parse_menu_pdf(image_bytes, restaurant_name)
    result = await _call_vision([image_bytes], restaurant_name)
    return result
