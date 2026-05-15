import requests
from datetime import datetime, timezone, timedelta

API_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
STORE_URL = "https://store.epicgames.com/p/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

MSK = timezone(timedelta(hours=3))


def parse_date(date_str):
    if not date_str:
        return None
    try:
        s = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt.astimezone(MSK).strftime("%d.%m.%Y")
    except Exception:
        return None


def get_epic_freebies():
    games = []
    params = {"locale": "en-US", "country": "US"}
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    elements = (
        data.get("data", {})
        .get("Catalog", {})
        .get("searchStore", {})
        .get("elements", [])
    )

    for item in elements:
        promotions = item.get("promotions")
        if not promotions:
            continue

        current_offers = promotions.get("promotionalOffers", [])
        if not current_offers:
            continue

        is_free = False
        end_date = None

        for offer_set in current_offers:
            for offer in offer_set.get("promotionalOffers", []):
                disc_pct = offer.get("discountSetting", {}).get("discountPercentage")
                if disc_pct != 0:
                    continue
                is_free = True
                end = offer.get("endDate")
                if end:
                    parsed = parse_date(end)
                    if parsed and (not end_date or parsed < end_date):
                        end_date = parsed

        if not is_free:
            continue

        slug = item.get("productSlug")
        if not slug:
            continue

        image = ""
        for img in item.get("keyImages", []):
            if img.get("type") in ("OfferImageWide", "Thumbnail"):
                image = img.get("url", "")
                if image:
                    break

        games.append({
            "store": "Epic Games",
            "id": item.get("id", ""),
            "name": item.get("title", "Unknown"),
            "url": STORE_URL.format(slug),
            "image": image,
            "end_date": end_date,
            "original_price": item.get("price", {}).get("totalPrice", {}).get("originalPrice", 0),
        })

    return games
