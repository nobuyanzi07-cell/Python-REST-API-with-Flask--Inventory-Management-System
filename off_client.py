import requests

BASE_URL = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "InventoryManager/1.0 (student project)"}
TIMEOUT = 10


class ExternalAPIError(Exception):
    """Raised when the OpenFoodFacts API cannot be reached or fails."""


def _normalize(product):
    return {
        "name": product.get("product_name") or "Unknown",
        "brand": product.get("brands", ""),
        "barcode": product.get("code") or product.get("_id", ""),
        "category": product.get("categories", ""),
        "ingredients": product.get("ingredients_text", ""),
    }


def _get(url, params=None):
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ExternalAPIError(str(exc))


def fetch_by_barcode(barcode):
    """Return a normalized product dict, or None if not found."""
    data = _get(f"{BASE_URL}/api/v2/product/{barcode}.json")
    if data.get("status") != 1:
        return None
    return _normalize(data["product"])


def search_by_name(name, limit=5):
    """Return a list of normalized product dicts (may be empty)."""
    data = _get(
        f"{BASE_URL}/cgi/search.pl",
        params={
            "search_terms": name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": limit,
        },
    )
    return [_normalize(p) for p in data.get("products", [])]