import requests
from datetime import datetime, timezone, timedelta

API_CATEGORIES = "https://store.steampowered.com/api/featuredcategories"
API_SEARCH = "https://store.steampowered.com/search/results/"

STORE_URL = "https://store.steampowered.com/app/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

MSK = timezone(timedelta(hours=3))


def check_100_percent_off(item):
    if item.get("discount_percent") != 100:
        return False
    orig = item.get("original_price", 0)
    return bool(orig) and orig > 0


def format_end_date(end_ts):
    if end_ts and end_ts > 0:
        return (
            datetime.fromtimestamp(end_ts, tz=timezone.utc)
            .astimezone(MSK)
            .strftime("%d.%m.%Y %H:%M")
        )
    return None


def game_from_item(item):
    return {
        "store": "Steam",
        "id": str(item["id"]),
        "name": item.get("name", "Unknown"),
        "url": STORE_URL.format(item["id"]),
        "image": item.get("header_image", ""),
        "end_date": format_end_date(item.get("discount_expiration")),
        "original_price": item.get("original_price", 0),
    }


def get_steam_freebies():
    games = []

    # Method 1: featuredcategories (specials section)
    try:
        resp = requests.get(
            API_CATEGORIES,
            params={"cc": "us", "l": "english"},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("specials", {}).get("items", []):
            if check_100_percent_off(item):
                games.append(game_from_item(item))
    except Exception as e:
        print(f"  featuredcategories error: {e}")

    # Method 2: search API with specials filter
    try:
        seen_ids = {g["id"] for g in games}
        resp = requests.get(
            API_SEARCH,
            params={"specials": 1, "json": 1, "count": 100, "cc": "us", "l": "english"},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            appid = str(item.get("id", ""))
            if appid and appid not in seen_ids and check_100_percent_off(item):
                seen_ids.add(appid)
                games.append(game_from_item(item))
    except Exception as e:
        print(f"  search API error: {e}")

    return games
